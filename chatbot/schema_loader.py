"""
Schema Loader
Auto-generate full schema reference from the live database.

Loaded once per process and cached forever — the generated text is
deterministic (sorted tables, ordinal column order), so the system
prompt prefix stays byte-identical across requests and restarts.
DeepSeek charges cache-hit pricing on the repeated prefix, so we can
afford to include every table and column.
"""
from typing import Dict, List, Optional
from .db_client import fetch_schema_columns

# Internal/ETL tables — not business data, hidden from the chatbot
EXCLUDE_TABLES = {'batch_sync_log', 'batch_table_config', 'query_templates'}

# Compact type names to save tokens
TYPE_ABBREV = {
    'integer': 'int',
    'bigint': 'int',
    'smallint': 'int',
    'numeric': 'num',
    'double precision': 'num',
    'real': 'num',
    'character varying': 'text',
    'character': 'text',
    'text': 'text',
    'date': 'date',
    'timestamp without time zone': 'ts',
    'timestamp with time zone': 'ts',
    'boolean': 'bool',
}

_schema_cache: Optional[Dict[str, List[Dict]]] = None
_reference_cache: Optional[str] = None


def load_schema() -> Dict[str, List[Dict]]:
    """
    Load {table_name: [{column_name, data_type}, ...]} from DB.
    Cached for process lifetime.
    """
    global _schema_cache
    if _schema_cache is None:
        schema: Dict[str, List[Dict]] = {}
        for col in fetch_schema_columns():
            table = col['table_name']
            if table in EXCLUDE_TABLES:
                continue
            schema.setdefault(table, []).append(col)
        _schema_cache = schema
    return _schema_cache


def get_business_tables() -> List[str]:
    """Sorted list of queryable business tables (= custom SQL whitelist)."""
    return sorted(load_schema().keys())


def build_schema_reference() -> str:
    """
    Build the full-schema markdown section for the system prompt.
    Compact format: one line of `col:type` pairs per table.
    """
    global _reference_cache
    if _reference_cache is not None:
        return _reference_cache

    schema = load_schema()
    lines = [
        "## 📚 Schema เต็มทุกตาราง (อ้างอิงสำหรับ query_custom)",
        "",
        "ทุกตารางด้านล่างใช้กับ query_custom ได้ — format: `column:type`",
        "(int=integer, num=numeric, ts=timestamp)",
        "",
    ]
    for table in sorted(schema.keys()):
        cols = schema[table]
        col_parts = [
            f"{c['column_name']}:{TYPE_ABBREV.get(c['data_type'], c['data_type'])}"
            for c in cols
        ]
        lines.append(f"### {table} ({len(cols)} คอลัมน์)")
        lines.append(", ".join(col_parts))
        lines.append("")

    _reference_cache = "\n".join(lines)
    return _reference_cache


if __name__ == "__main__":
    ref = build_schema_reference()
    tables = get_business_tables()
    print(f"Tables: {len(tables)}")
    print(f"Reference: {len(ref)} chars (~{len(ref) // 4} tokens)")
    print(ref[:2000])
