"""
Supabase Client
Uses Supabase REST API (HTTPS) instead of direct PostgreSQL connection
This bypasses IPv6 connectivity issues on Railway
"""
from supabase import create_client, Client
from typing import Dict, List, Any, Optional
import json

# Initialize Supabase client (lazy loaded)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance
    Returns: Supabase client
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    import os
    from dotenv import load_dotenv
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")

    _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client


def query_templates() -> List[Dict[str, Any]]:
    """
    Fetch all query templates from database via REST API

    Returns:
        List of template dicts with fields: id, name, description, sql_template, params
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table('query_templates') \
            .select('id, name, description, sql_template, params') \
            .order('id') \
            .execute()

        return response.data

    except Exception as e:
        raise Exception(f"Failed to fetch templates from Supabase: {str(e)}")


def execute_sql_template(template_name: str, sql_template: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute a SQL template via Supabase RPC (HTTPS, IPv4 compatible)

    Args:
        template_name: Name of the template (for logging)
        sql_template: SQL query with :param placeholders (not used directly, kept for API compat)
        params: Dictionary of parameter values

    Returns:
        List of result rows as dicts
    """
    try:
        supabase = get_supabase_client()

        # Convert params to JSON-serializable format
        # Replace None with "null" string for SQL handling
        clean_params = {}
        for k, v in params.items():
            if v is None:
                clean_params[k] = "null"
            else:
                clean_params[k] = str(v)

        # Call the execute_template function via RPC
        response = supabase.rpc(
            'execute_template',
            {
                'p_template_name': template_name,
                'p_params': clean_params
            }
        ).execute()

        result = response.data

        if isinstance(result, dict):
            if result.get('success'):
                return result.get('rows', [])
            else:
                raise Exception(result.get('error', 'Unknown error'))

        # If result is already a list, return it
        if isinstance(result, list):
            return result

        return []

    except Exception as e:
        raise Exception(f"Failed to execute template '{template_name}': {str(e)}")


def test_connection() -> Dict[str, Any]:
    """
    Test Supabase connection

    Returns:
        Dict with connection status and template count
    """
    try:
        templates = query_templates()

        return {
            "success": True,
            "message": "Supabase REST API connection successful (IPv4 compatible)",
            "template_count": len(templates),
            "templates": [t['name'] for t in templates]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test connection when run directly
    result = test_connection()

    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"📊 Found {result['template_count']} templates:")
        for name in result['templates']:
            print(f"  - {name}")
    else:
        print(f"❌ Connection failed: {result['error']}")
