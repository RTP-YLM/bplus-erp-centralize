import pyodbc

# MSSQL → PostgreSQL type mapping
_TYPE_MAP = {
    'int':             'INTEGER',
    'bigint':          'BIGINT',
    'smallint':        'SMALLINT',
    'tinyint':         'SMALLINT',
    'bit':             'BOOLEAN',
    'money':           'NUMERIC(18,4)',
    'smallmoney':      'NUMERIC(10,4)',
    'decimal':         'NUMERIC',
    'numeric':         'NUMERIC',
    'float':           'DOUBLE PRECISION',
    'real':            'REAL',
    'date':            'DATE',
    'datetime':        'TIMESTAMP',
    'datetime2':       'TIMESTAMP',
    'smalldatetime':   'TIMESTAMP',
    'nvarchar':        'TEXT',
    'varchar':         'TEXT',
    'nchar':           'TEXT',
    'char':            'TEXT',
    'ntext':           'TEXT',
    'text':            'TEXT',
    'uniqueidentifier':'UUID',
    'varbinary':       'BYTEA',
    'image':           'BYTEA',
}


def get_conn(branch):
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={branch['mssql_host']},{branch['mssql_port']};"
        f"DATABASE={branch['mssql_db']};"
        f"UID={branch['mssql_user']};"
        f"PWD={branch['mssql_pass']};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=30)


def get_columns(conn, table_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, table_name)
    return [
        {'name': row[0], 'pg_type': _TYPE_MAP.get(row[1].lower(), 'TEXT')}
        for row in cur.fetchall()
    ]


def get_watermark(conn, table_name, watermark_col, watermark_type):
    cur = conn.cursor()
    if watermark_type == 'integer':
        cur.execute(f"SELECT MAX([{watermark_col}]) FROM [{table_name}]")
    elif watermark_type == 'datetime':
        cur.execute(f"SELECT MAX([{watermark_col}]) FROM [{table_name}]")
    else:  # lastupd — stored as nvarchar numeric string
        cur.execute(f"SELECT MAX(CAST([{watermark_col}] AS BIGINT)) FROM [{table_name}]")
    row = cur.fetchone()
    return str(row[0]) if row and row[0] is not None else None


def _parse_watermark_datetime(val):
    """Convert stored watermark string back to a Python datetime for safe parameter binding."""
    if isinstance(val, str):
        from datetime import datetime as _dt
        # handle both '2026-06-04 00:00:00' and '2026-06-04T00:00:00' formats
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
            try:
                return _dt.strptime(val, fmt)
            except ValueError:
                continue
        # fallback — let pyodbc/SQL Server handle isoformat
        return _dt.fromisoformat(val)
    return val  # already a datetime object


def extract(conn, table_name, watermark_col, watermark_type, last_watermark, batch_size=1000):
    """Yields (column_names, rows) batches."""
    cur = conn.cursor()

    if not watermark_col or last_watermark is None:
        cur.execute(f"SELECT * FROM [{table_name}]")
    elif watermark_type == 'integer':
        cur.execute(
            f"SELECT * FROM [{table_name}] WHERE [{watermark_col}] > ?",
            int(last_watermark)
        )
    elif watermark_type == 'datetime':
        cur.execute(
            f"SELECT * FROM [{table_name}] WHERE [{watermark_col}] > ?",
            _parse_watermark_datetime(last_watermark)
        )
    else:  # lastupd (bigint-as-nvarchar)
        cur.execute(
            f"SELECT * FROM [{table_name}] "
            f"WHERE CAST([{watermark_col}] AS BIGINT) > CAST(? AS BIGINT)",
            last_watermark
        )

    col_names = [d[0] for d in cur.description]
    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break
        yield col_names, rows
