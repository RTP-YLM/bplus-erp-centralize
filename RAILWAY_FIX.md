# Database Migration: Supabase → Railway PostgreSQL

## Background

The chatbot originally ran on Railway but could not reach Supabase PostgreSQL
directly (Supabase's `db.*.supabase.co` endpoint is **IPv6-only** and Railway has
no IPv6 outbound), so we worked around it with the Supabase REST/RPC client.

We are now hosting PostgreSQL **on Railway itself**, so the workaround is no longer
needed: the chatbot connects to the database with a plain `psycopg2` connection
over `PG_DSN`. This is simpler, removes the `supabase` dependency, and keeps the
data, app, and ETL on one platform.

## Architecture after migration

```
MSSQL (8 BPLUSERP DBs)
   │  pyodbc
   ▼
ETL (etl/*)  ──psycopg2──►  Railway PostgreSQL  ◄──psycopg2──  Chatbot (chatbot/*)
                              (single PG_DSN)                      │
                                                                   ▼
                                                          Claude → LINE
```

Both the ETL and the chatbot share one `PG_DSN`. No REST API, no RPC layer.

## Code changes

| File | Change |
|------|--------|
| `chatbot/db_client.py` | **New.** Direct `psycopg2` client. `query_templates()`, `get_branches()`, `execute_sql_template()` (does `:param → %s` substitution in Python). |
| `chatbot/runner.py` | Import `execute_sql_template` from `db_client`. |
| `chatbot/templates.py` | Load templates via `db_client`. |
| `chatbot/system_prompt.py` | Load branches via `db_client`. |
| `chatbot/supabase_client.py` | **Removed.** |
| `requirements.txt` | Removed `supabase>=2.9.0`. |
| `.env.example` | `PG_DSN` points at the Railway database. |

> The Supabase `execute_template` RPC function is **not** migrated — `db_client`
> parameterizes SQL itself, so the database needs no helper function.

## Data migration (clone)

The full schema + data is copied from Supabase to Railway with `pg_dump | pg_restore`.
See `scripts/clone_to_railway.sh`. The ETL code itself is unchanged — pointing its
`PG_DSN` at Railway is all that is required for future syncs.

## Environment

```bash
# Railway PostgreSQL (direct psycopg2 connection)
PG_DSN=postgresql://postgres:<password>@<host>.proxy.rlwy.net:<port>/railway

ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-haiku-4-5
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_CHANNEL_SECRET=...
LINE_DESTINATION_USER_ID=...
```
