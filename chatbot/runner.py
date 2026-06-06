"""
SQL Template Runner
Execute parameterized SQL queries
"""
from typing import Dict, List, Any, Optional
from .templates import get_template
from .supabase_client import execute_sql_template


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
    Format query results for Claude consumption

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
