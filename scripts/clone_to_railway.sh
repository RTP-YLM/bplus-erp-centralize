#!/usr/bin/env bash
#
# Clone the entire database from Supabase → Railway PostgreSQL.
#
# Usage:
#   SRC_DSN="postgresql://postgres:PASS@db.xxxx.supabase.co:5432/postgres" \
#   DST_DSN="postgresql://postgres:PASS@xxx.proxy.rlwy.net:PORT/railway" \
#   ./scripts/clone_to_railway.sh
#
# Requires: pg_dump / pg_restore (postgresql-client) matching the server major
# version (both are PostgreSQL 17.x). Check with: pg_dump --version
#
set -euo pipefail

# Use the PostgreSQL 17 client to match the servers (both are PG 17.x).
PG_BIN="${PG_BIN:-/opt/homebrew/opt/postgresql@17/bin}"
PG_DUMP="$PG_BIN/pg_dump"
PG_RESTORE="$PG_BIN/pg_restore"
PSQL="$PG_BIN/psql"

SRC_DSN="${SRC_DSN:?Set SRC_DSN to the Supabase PG_DSN (source)}"
DST_DSN="${DST_DSN:?Set DST_DSN to the Railway PG_DSN (target)}"

DUMP_FILE="${DUMP_FILE:-/tmp/bplus_clone_$(date +%Y%m%d_%H%M%S).dump}"

echo "==> Source : ${SRC_DSN%%:*}://***@${SRC_DSN##*@}"
echo "==> Target : ${DST_DSN%%:*}://***@${DST_DSN##*@}"
echo "==> Dump   : $DUMP_FILE"
echo

# 1. Dump source — custom format (-Fc) so we can restore in parallel and skip
#    Supabase-internal schemas. Only the public schema holds our app data.
echo "==> [1/3] pg_dump (public schema, data + DDL)..."
"$PG_DUMP" "$SRC_DSN" \
  --format=custom \
  --no-owner --no-privileges \
  --schema=public \
  --file="$DUMP_FILE"

echo "    dump size: $(du -h "$DUMP_FILE" | cut -f1)"

# 2. Restore into Railway. --clean --if-exists makes the run idempotent so it can
#    be re-run safely; -j speeds up large tables (TRANSTKD/SKUMOVE/DOCINFO).
echo "==> [2/3] pg_restore into Railway..."
"$PG_RESTORE" \
  --dbname="$DST_DSN" \
  --no-owner --no-privileges \
  --clean --if-exists \
  --jobs=4 \
  "$DUMP_FILE"

# 3. Sanity check row counts on the heavy tables.
echo "==> [3/3] verify row counts on Railway..."
"$PSQL" "$DST_DSN" -c "
  SELECT 'query_templates' t, count(*) FROM query_templates
  UNION ALL SELECT 'batch_branch', count(*) FROM batch_branch
  UNION ALL SELECT 'batch_table_config', count(*) FROM batch_table_config
  UNION ALL SELECT 'DOCINFO', count(*) FROM \"DOCINFO\"
  UNION ALL SELECT 'TRANSTKD', count(*) FROM \"TRANSTKD\"
  UNION ALL SELECT 'SKUMOVE', count(*) FROM \"SKUMOVE\"
  ORDER BY 1;
"

echo
echo "==> Done. Point PG_DSN in .env at the Railway database to cut over."
