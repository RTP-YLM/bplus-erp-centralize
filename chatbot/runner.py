"""
SQL Template Runner + Custom Query Runner
Execute parameterized SQL queries with validation.
"""
import re
from typing import Dict, List, Any
from .templates import get_template
from .db_client import execute_sql_template, execute_raw_sql


# ── Whitelist tables for custom queries ──────────────────────────
WHITELIST_TABLES = [
    'docinfo', 'transtkd', 'transtkh', 'transtk',
    'arfile', 'apfile', 'arpayment', 'appayment',
    'skumaster', 'skubalance', 'skumove',
    'goods', 'goodsunit', 'sku', 'skuap', 'arplu',
    'brand', 'doctype', 'glperiod', 'companyinfo',
    'accountchart', 'salesman',
    'bankfile', 'bankstatement', 'paymenttype',
    'branch', 'batch_branch', 'ardetail', 'apdetail',
    'tranpayh', 'tranpayd', 'tranpaya',
    'accountvoucher', 'accountjournal', 'vattable',
    'cashbook', 'sldetail',
]

BANNED_KEYWORDS = [
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
    'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE',
    'REPLACE', 'MERGE', 'INTO', 'CALL',
]

MAX_CUSTOM_ROWS = 100


def validate_custom_sql(sql: str) -> str:
    """
    Validate a custom SQL query.
    Returns cleaned SQL, or raises ValueError.
    """
    sql_stripped = sql.strip().rstrip(';')
    sql_upper = sql_stripped.upper()

    # 1. Must be SELECT
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
        raise ValueError("เฉพาะ SELECT เท่านั้น — พบ: " + sql_stripped[:50])

    # 2. No dangerous keywords
    for kw in BANNED_KEYWORDS:
        if re.search(r'\b' + kw + r'\b', sql_upper):
            raise ValueError(f"ไม่อนุญาตคำสั่ง '{kw}' ใน custom query")

    # 3. No semicolons (multi-statement injection)
    if ';' in sql_stripped:
        raise ValueError("ไม่อนุญาต multiple statements (;)")

    # 4. Check tables against whitelist
    # Extract table names from FROM + JOIN clauses (handle aliases)
    table_pattern = re.compile(
        r'\b(?:FROM|JOIN)\s+(\w+)',
        re.IGNORECASE
    )
    referenced = table_pattern.findall(sql_stripped)
    whitelist_lower = [t.lower() for t in WHITELIST_TABLES]

    # CTE names (WITH clause) — skip them
    cte_names = set()
    cte_match = re.match(r'\s*WITH\s+(\w+)\s+AS\s*\(', sql_stripped, re.IGNORECASE)
    if cte_match:
        cte_names.add(cte_match.group(1).lower())

    for t in referenced:
        t_lower = t.lower()
        # Skip CTE names and subquery aliases
        if t_lower in cte_names:
            continue
        # Skip obvious aliases (single letters, common alias patterns)
        if len(t_lower) <= 2 or t_lower.startswith('_'):
            continue
        if t_lower not in whitelist_lower:
            raise ValueError(f"ตาราง '{t}' ไม่อยู่ใน whitelist — ใช้เฉพาะตารางใน ERP schema")

    # 5. Add LIMIT if missing
    if 'LIMIT' not in sql_upper:
        sql_stripped += f' LIMIT {MAX_CUSTOM_ROWS}'
    else:
        # Extract existing LIMIT value and cap it
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
        if limit_match:
            existing_limit = int(limit_match.group(1))
            if existing_limit > MAX_CUSTOM_ROWS:
                sql_stripped = re.sub(
                    r'LIMIT\s+\d+',
                    f'LIMIT {MAX_CUSTOM_ROWS}',
                    sql_stripped,
                    count=1,
                    flags=re.IGNORECASE
                )

    return sql_stripped


def run_custom_sql(sql: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a custom SQL query with validation.

    Args:
        sql: SQL SELECT statement with :param placeholders
        params: Parameter values (date_from, date_to, branch_id, etc.)

    Returns:
        {"success": bool, "rows": list, "row_count": int, "error": str|None}
    """
    # Validate
    try:
        sql_clean = validate_custom_sql(sql)
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "rows": [],
            "row_count": 0
        }

    # Clean up params — remove None values for optional params
    clean_params = {k: v for k, v in params.items() if v is not None}
    # But keep :branch_id as None if explicitly passed
    if 'branch_id' not in clean_params:
        clean_params['branch_id'] = None

    try:
        rows = execute_raw_sql(sql_clean, clean_params)
        return {
            "success": True,
            "rows": rows,
            "row_count": len(rows),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "rows": [],
            "row_count": 0
        }


def run_sql_template(template_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a SQL template with parameters

    Args:
        template_name: Name of the template to execute
        params: Dictionary of parameter values

    Returns:
        {
            "success": bool,
            "rows": list of dicts (if success),
            "row_count": int,
            "error": str (if not success)
        }
    """
    # Get template
    template = get_template(template_name)
    if not template:
        return {
            "success": False,
            "error": f"Template '{template_name}' not found",
            "rows": [],
            "row_count": 0
        }

    sql_template = template['sql_template']

    # Prepare params with defaults
    final_params = {}
    for param_def in template['params']:
        param_name = param_def['name']
        param_value = params.get(param_name)

        # Handle None for optional params
        if param_value is None and not param_def.get('required', False):
            final_params[param_name] = None
        else:
            final_params[param_name] = param_value

    # Handle special defaults for limit_rows
    if 'limit_rows' in final_params and final_params['limit_rows'] is None:
        if template_name in ['query_documents_today']:
            final_params['limit_rows'] = 50
        elif template_name in ['query_top_customers', 'query_top_skus']:
            final_params['limit_rows'] = 10

    # Execute query using Supabase client
    try:
        rows = execute_sql_template(template_name, sql_template, final_params)

        return {
            "success": True,
            "rows": rows,
            "row_count": len(rows),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "rows": [],
            "row_count": 0
        }


def format_rows_for_claude(rows: List[Dict[str, Any]], row_count: int = None) -> str:
    """
    Format query results for LLM consumption

    Args:
        rows: List of result rows
        row_count: Optional total count (if different from len(rows))

    Returns:
        Formatted string representation
    """
    if not rows:
        return "ไม่พบข้อมูล"

    # Simple text representation
    lines = []
    lines.append(f"พบ {row_count or len(rows)} แถว:\n")

    # Show first 50 rows max
    display_rows = rows[:50]

    # Get column names from first row
    if display_rows:
        headers = list(display_rows[0].keys())

        # Format as simple list
        for i, row in enumerate(display_rows, 1):
            row_parts = [f"{k}: {v}" for k, v in row.items()]
            lines.append(f"{i}. {', '.join(row_parts)}")

    return "\n".join(lines)
