import logging
from . import config_loader, extractor, loader

log = logging.getLogger(__name__)


def _sync_one(branch, table_cfg, pg_conn, force_full=False):
    table      = table_cfg['table_name']
    frequency  = table_cfg['frequency']
    sync_type  = 'fullload' if force_full else table_cfg['sync_type']
    wm_col     = table_cfg['watermark_col']
    wm_type    = table_cfg['watermark_type'] or 'lastupd'
    pk_cols    = table_cfg['pk_columns']
    batch_size = table_cfg['batch_size']
    branch_id  = branch['id']

    # 'once' tables: skip if already done
    if frequency == 'once' and not force_full:
        if config_loader.is_already_synced(branch_id, table):
            log.info(f"  skip  {table} (once, already synced)")
            return

    last_wm   = None if sync_type == 'fullload' else config_loader.get_last_watermark(branch_id, table)
    log_id    = config_loader.start_log(branch_id, table, sync_type, last_wm)
    rows_ext  = rows_ups = 0
    new_wm    = last_wm

    try:
        mssql = extractor.get_conn(branch)

        columns = extractor.get_columns(mssql, table)
        loader.ensure_table(pg_conn, table, columns, pk_cols)

        if sync_type == 'fullload':
            loader.truncate_branch(pg_conn, table, branch_id)

        for col_names, rows in extractor.extract(mssql, table, wm_col, wm_type, last_wm, batch_size):
            rows_with_bid = [(branch_id,) + tuple(r) for r in rows]
            rows_ups += loader.upsert(pg_conn, table, col_names, rows_with_bid, pk_cols)
            rows_ext += len(rows)

        if wm_col:
            new_wm = extractor.get_watermark(mssql, table, wm_col, wm_type)

        mssql.close()
        config_loader.finish_log(log_id, 'success', rows_ext, rows_ups, new_wm)
        log.info(f"  ✓ {table:20s}  extracted={rows_ext:>7,}  upserted={rows_ups:>7,}")

    except Exception as exc:
        # Rollback any aborted transaction so pg_conn stays usable for next table
        try:
            pg_conn.rollback()
        except Exception:
            pass
        config_loader.finish_log(log_id, 'failed', rows_ext, rows_ups, new_wm, str(exc))
        log.error(f"  ✗ {table}: {exc}")
        # Don't re-raise — orchestrator already continues, rollback is enough


def run(frequency='daily', branch_id=None, table_name=None, force_full=False):
    branches = config_loader.get_branches(branch_id)
    tables   = config_loader.get_table_configs(frequency, table_name)

    if not branches:
        log.warning("No enabled branches found.")
        return
    if not tables:
        log.warning("No enabled tables found for frequency=%s.", frequency)
        return

    log.info(f"Batch start — branches={len(branches)}  tables={len(tables)}  "
             f"frequency={frequency}  force_full={force_full}")

    for branch in branches:
        log.info(f"Branch [{branch['id']}] {branch['name']} ({branch['mssql_db']})")
        pg_conn = loader.get_conn()
        try:
            for cfg in tables:
                try:
                    _sync_one(branch, cfg, pg_conn, force_full)
                except Exception:
                    continue  # error already logged; keep going
        finally:
            pg_conn.close()

    log.info("Batch complete.")
