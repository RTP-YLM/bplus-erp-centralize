from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
from .settings import PG_DSN


def get_conn():
    return psycopg2.connect(PG_DSN)


def ensure_table(conn, table_name, columns, pk_columns):
    """Auto-create target table from source column list if it doesn't exist."""
    pk_lower = [c.lower() for c in pk_columns]          # MSSQL→PG lowercase
    col_defs = ['branch_id SMALLINT NOT NULL']
    for col in columns:
        col_defs.append(f'"{col["name"].lower()}" {col["pg_type"]}')
    col_defs.append('synced_at TIMESTAMPTZ DEFAULT now()')

    pk_str = ', '.join(f'"{c}"' for c in pk_lower)

    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS "{table_name.lower()}" (
                {', '.join(col_defs)},
                PRIMARY KEY ({pk_str})
            )
        """)
    conn.commit()


def truncate_branch(conn, table_name, branch_id):
    with conn.cursor() as cur:
        cur.execute(f'DELETE FROM "{table_name.lower()}" WHERE branch_id = %s', (branch_id,))
    conn.commit()


def drop_table(conn, table_name):
    """Drop table if it exists (for schema repair on fullload)."""
    with conn.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS "{table_name.lower()}"')
    conn.commit()


def upsert(conn, table_name, col_names, rows_with_branch_id, pk_columns):
    """
    rows_with_branch_id: list of tuples where first element is branch_id,
                         followed by original MSSQL column values.
    """
    if not rows_with_branch_id:
        return 0

    pk_lower = [c.lower() for c in pk_columns]          # MSSQL→PG lowercase
    now = datetime.now(timezone.utc)
    target_cols = ['branch_id'] + [c.lower() for c in col_names] + ['synced_at']
    update_cols = [c for c in target_cols if c not in pk_lower]

    col_list  = ', '.join(f'"{c}"' for c in target_cols)
    pk_str    = ', '.join(f'"{c}"' for c in pk_lower)
    val_str   = ', '.join(['%s'] * len(target_cols))
    upd_str   = ', '.join(f'"{c}" = EXCLUDED."{c}"' for c in update_cols)

    sql = f"""
        INSERT INTO "{table_name.lower()}" ({col_list})
        VALUES ({val_str})
        ON CONFLICT ({pk_str}) DO UPDATE SET {upd_str}
    """

    data = [tuple(row) + (now,) for row in rows_with_branch_id]

    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, data, page_size=500)
    conn.commit()
    return len(data)
