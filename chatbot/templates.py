"""
Query Templates Loader
Load and cache SQL templates from database
"""
from typing import Dict, List, Optional
from .db_client import query_templates as fetch_templates_from_db

# In-memory cache
_templates_cache: Optional[Dict[str, dict]] = None
_templates_loaded_at: float = 0


def load_templates() -> Dict[str, dict]:
    """
    Load all query templates from database.
    Returns dict: {template_name: {id, name, description, sql_template, params}}
    Cache refreshes every 5 minutes.
    """
    global _templates_cache, _templates_loaded_at

    now = __import__('time').time()
    if _templates_cache is not None and _templates_loaded_at > 0:
        if now - _templates_loaded_at < 300:  # 5 min TTL
            return _templates_cache

    rows = fetch_templates_from_db()

    _templates_cache = {
        row['name']: dict(row)
        for row in rows
    }
    _templates_loaded_at = now

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
