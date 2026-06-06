import psycopg2
import psycopg2.extras
from .settings import PG_DSN


def _conn():
    return psycopg2.connect(PG_DSN)


def get_branches(branch_id=None):
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        sql = "SELECT * FROM batch_branch WHERE enabled = true"
        params = []
        if branch_id:
            sql += " AND id = %s"
            params.append(branch_id)
        sql += " ORDER BY id"
        cur.execute(sql, params)
        return cur.fetchall()


def get_table_configs(frequency=None, table_name=None):
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        sql = "SELECT * FROM batch_table_config WHERE enabled = true"
        params = []
        if frequency:
            sql += " AND frequency = %s"
            params.append(frequency)
        if table_name:
            sql += " AND UPPER(table_name) = UPPER(%s)"
            params.append(table_name)
        sql += " ORDER BY priority, table_name"
        cur.execute(sql, params)
        return cur.fetchall()


def get_last_watermark(branch_id, table_name):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT watermark_to FROM batch_sync_log
            WHERE branch_id = %s AND table_name = %s AND status = 'success'
            ORDER BY finished_at DESC LIMIT 1
        """, (branch_id, table_name))
        row = cur.fetchone()
        return row[0] if row else None


def is_already_synced(branch_id, table_name):
    """For 'once' tables — check if ever completed successfully."""
    return get_last_watermark(branch_id, table_name) is not None or _has_success(branch_id, table_name)


def _has_success(branch_id, table_name):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM batch_sync_log
            WHERE branch_id = %s AND table_name = %s AND status = 'success'
            LIMIT 1
        """, (branch_id, table_name))
        return cur.fetchone() is not None


def start_log(branch_id, table_name, sync_type, watermark_from):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO batch_sync_log (branch_id, table_name, sync_type, status, watermark_from)
            VALUES (%s, %s, %s, 'running', %s) RETURNING id
        """, (branch_id, table_name, sync_type, str(watermark_from) if watermark_from is not None else None))
        conn.commit()
        return cur.fetchone()[0]


def finish_log(log_id, status, rows_extracted, rows_upserted, watermark_to, error_msg=None):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            UPDATE batch_sync_log SET
                status         = %s,
                rows_extracted = %s,
                rows_upserted  = %s,
                watermark_to   = %s,
                error_msg      = %s,
                finished_at    = now()
            WHERE id = %s
        """, (
            status, rows_extracted, rows_upserted,
            str(watermark_to) if watermark_to is not None else None,
            error_msg, log_id
        ))
        conn.commit()
