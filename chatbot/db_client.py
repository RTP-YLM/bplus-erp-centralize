"""
Database Client (Railway PostgreSQL)
Uses psycopg2 ThreadedConnectionPool — thread-safe for FastAPI/uvicorn.
"""
import os
import re
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

_pool: Optional[pool.ThreadedConnectionPool] = None


def _get_pool() -> pool.ThreadedConnectionPool:
    """Lazy-init ThreadedConnectionPool (thread-safe)."""
    global _pool
    if _pool is None:
        load_dotenv()
        pg_dsn = os.getenv("PG_DSN")
        if not pg_dsn:
            raise ValueError("PG_DSN environment variable is required")
        _pool = pool.ThreadedConnectionPool(1, 5, pg_dsn)
    return _pool


def query_templates() -> List[Dict[str, Any]]:
    """Fetch all query templates from database."""
    p = _get_pool()
    conn = p.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "SELECT id, name, description, sql_template, params "
            "FROM query_templates ORDER BY id"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        p.putconn(conn)


def fetch_schema_columns() -> List[Dict[str, Any]]:
    """
    Fetch all public table columns in deterministic order.
    Used to build the full-schema prompt section — ordering must be
    stable so the prompt prefix stays byte-identical (DeepSeek cache).
    """
    p = _get_pool()
    conn = p.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "SELECT c.table_name, c.column_name, c.data_type "
            "FROM information_schema.columns c "
            "JOIN information_schema.tables t "
            "  ON t.table_name = c.table_name AND t.table_schema = c.table_schema "
            "WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE' "
            "ORDER BY c.table_name, c.ordinal_position"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        p.putconn(conn)


def get_branches() -> List[Dict[str, Any]]:
    """Fetch enabled branches."""
    p = _get_pool()
    conn = p.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "SELECT id, name, branch_code, enabled "
            "FROM batch_branch WHERE enabled = true ORDER BY id"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        p.putconn(conn)


def _build_replacer(params: Dict[str, Any]):
    """
    Build a regex + callback pair that replaces :param → %s in order,
    with longest param names matched first (prevents :date eating :date_from).

    If a :param appears in SQL but not in params dict, it's replaced with NULL.

    params: {'customer': 'เม้ง', 'date_from': '2026-01-01', ...}
    """
    # Sort param names longest-first so :date_from is matched before :date
    # (?<!:) skips PostgreSQL type casts — ::date must NOT match as :date
    sorted_names = sorted(params.keys(), key=len, reverse=True)
    pattern = re.compile(r'(?<!:):(' + '|'.join(map(re.escape, sorted_names)) + r')\b')

    values = []
    missing_params = set()

    def _repl(m):
        name = m.group(1)
        val = params.get(name)
        if val is None or val == "null":
            values.append(None)
        elif name == "limit_rows":
            values.append(int(val))
        elif name == "branch_id":
            values.append(int(val) if val else None)
        else:
            values.append(str(val))
        return "%s"

    def _clean(sql: str) -> str:
        """Replace known params, then catch any remaining :params → NULL."""
        result = sql
        if sorted_names:
            result = pattern.sub(_repl, result)
        # Second pass: catch any :params that weren't in the dict
        # (?<!:) skips ::type casts here too
        remaining = set(re.findall(r'(?<!:):(\w+)\b', result))
        if remaining:
            missing_params.update(remaining)
            for name in sorted(remaining, key=len, reverse=True):
                p = re.compile(r'(?<!:):' + re.escape(name) + r'\b')
                count = [0]
                def _repl2(m):
                    count[0] += 1
                    values.append(None)
                    return '%s'
                result = p.sub(_repl2, result)
        if missing_params:
            print(f"[WARN] Unknown params in SQL → replaced with NULL: {missing_params}")
        return result

    # Store _clean for use by execute_raw_sql
    return _clean, values


def execute_sql_template(
    template_name: str,
    sql_template: str,
    params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Execute a SQL template with :param → %s parameterized substitution.

    Args:
        template_name: Template name (for logging)
        sql_template: SQL with :param placeholders
        params: Parameter values

    Returns:
        List of result rows as dicts
    """
    return execute_raw_sql(sql_template, params)


def execute_raw_sql(
    sql: str,
    params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query with :param → %s parameterized substitution.

    Args:
        sql: SQL with :param placeholders
        params: Parameter values

    Returns:
        List of result rows as dicts
    """
    _clean, values = _build_replacer(params)

    sql_clean = _clean(sql)

    # Clean up PostgreSQL escaped quotes: ''%'' → '%' for ILIKE patterns.
    # Templates store ''%'' || :customer || ''%'' because '' is PostgreSQL's
    # literal single-quote escape. We resolve it here instead of changing 15 templates.
    # NOTE: Do NOT blindly replace '' → ' — that corrupts legitimate empty
    # strings like COALESCE(:x, '').
    sql_clean = sql_clean.replace("''%''", "'%'")

    # Escape literal % signs for psycopg2 (ILIKE '%' → ILIKE '%%').
    # psycopg2 treats % as a format placeholder; %% is the literal percent.
    # Use negative lookahead: replace % only when NOT followed by s (preserve %s).
    sql_clean = re.sub(r'%(?!s)', '%%', sql_clean)

    p = _get_pool()
    conn = p.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(sql_clean, values)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        raise Exception(f"Failed to execute query: {str(e)}")
    finally:
        cur.close()
        p.putconn(conn)


def test_connection() -> Dict[str, Any]:
    """Test database connection."""
    try:
        templates = query_templates()
        branches = get_branches()

        return {
            "success": True,
            "message": "Railway PostgreSQL connection successful",
            "template_count": len(templates),
            "templates": [t["name"] for t in templates],
            "branch_count": len(branches),
            "branches": [b["name"] for b in branches],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    result = test_connection()
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"📊 Templates: {result['template_count']}")
        print(f"🏢 Branches: {result['branch_count']}")
    else:
        print(f"❌ Connection failed: {result['error']}")
