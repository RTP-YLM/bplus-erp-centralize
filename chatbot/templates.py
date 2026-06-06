"""
Query Templates Loader
Load and cache SQL templates from database
"""
from typing import Dict, List, Optional
from .supabase_client import query_templates as fetch_templates_from_supabase

# In-memory cache
_templates_cache: Optional[Dict[str, dict]] = None


def load_templates() -> Dict[str, dict]:
    """
    Load all query templates from database
    Returns dict: {template_name: {id, name, description, sql_template, params}}
    """
    global _templates_cache

    if _templates_cache is not None:
        return _templates_cache

    # Fetch from Supabase REST API (uses HTTPS, works on Railway)
    rows = fetch_templates_from_supabase()

    _templates_cache = {
        row['name']: dict(row)
        for row in rows
    }

    return _templates_cache


def get_template(name: str) -> Optional[dict]:
    """
    Get a single template by name
    Returns: template dict or None if not found
    """
    templates = load_templates()
    return templates.get(name)


def list_templates() -> List[dict]:
    """
    List all available templates
    Returns: list of template dicts
    """
    templates = load_templates()
    return [
        {
            "name": t["name"],
            "description": t["description"]
        }
        for t in templates.values()
    ]


def reload_templates():
    """
    Force reload templates from database (clear cache)
    """
    global _templates_cache
    _templates_cache = None
    load_templates()
