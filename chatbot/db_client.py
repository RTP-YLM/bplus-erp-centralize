"""
Database Client (Railway PostgreSQL)
Uses direct psycopg2 connection — no Supabase dependency.
"""
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv

_conn: Optional[psycopg2.extensions.connection] = None


def get_connection() -> psycopg2.extensions.connection:
    """Get or create a psycopg2 connection from PG_DSN."""
    global _conn

    if _conn is not None and not _conn.closed:
        try:
            cur = _conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return _conn
        except Exception:
            _conn = None

    load_dotenv()
    pg_dsn = os.getenv("PG_DSN")
    if not pg_dsn:
        raise ValueError("PG_DSN environment variable is required")

    _conn = psycopg2.connect(pg_dsn)
    _conn.autocommit = True
    return _conn


def query_templates() -> List[Dict[str, Any]]:
    """Fetch all query templates from database."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "SELECT id, name, description, sql_template, params "
            "FROM query_templates ORDER BY id"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()


def get_branches() -> List[Dict[str, Any]]:
    """Fetch enabled branches."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "SELECT id, name, branch_code, enabled "
            "FROM batch_branch WHERE enabled = true ORDER BY id"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()


def execute_sql_template(
    template_name: str,
    sql_template: str,
    params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Execute a SQL template with :param → $N parameterized substitution.

    Args:
        template_name: Template name (for logging)
        sql_template: SQL with :param placeholders
        params: Parameter values

    Returns:
        List of result rows as dicts
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # Convert :param → %s (psycopg2 parameterized)
        # Replace :param_name with %s, collect values in order
        import re

        param_names = re.findall(r':(\w+)', sql_template)
        sql_clean = sql_template

        # Build ordered values aligned with %s placeholders
        values = []
        for name in param_names:
            sql_clean = sql_clean.replace(f":{name}", "%s", 1)
            val = params.get(name)
            # Handle null/None for optional params
            if val is None or val == "null":
                values.append(None)
            elif name == "limit_rows":
                values.append(int(val))
            elif name == "branch_id":
                values.append(int(val) if val else None)
            else:
                values.append(str(val))

        # Replace remaining PostgreSQL-style escaped quotes
        sql_clean = sql_clean.replace("''%''", "'%'")
        sql_clean = sql_clean.replace("''", "'")

        cur.execute(sql_clean, values)
        return [dict(r) for r in cur.fetchall()]

    except Exception as e:
        raise Exception(f"Failed to execute template '{template_name}': {str(e)}")
    finally:
        cur.close()


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
