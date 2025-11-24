#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
MANAGE_PY="$PROJECT_ROOT/manage.py"
SQLITE_PATH="$PROJECT_ROOT/db.dev.sqlite3"
TMP_DIR="$PROJECT_ROOT/tmp/sync_prod"
DUMP_FILE="$TMP_DIR/prod_dump.sql"
PYTHON_BIN="${PYTHON:-python3}"

log() {
  printf '\n[prod->sqlite] %s\n' "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

confirm() {
  local prompt="$1"
  read -r -p "$prompt (yes/no): " response
  if [[ "$response" != "yes" ]]; then
    echo "Aborted."
    exit 0
  fi
}

confirm "This will dump production data and overwrite the local SQLite database. Continue" 

require_cmd pg_dump
require_cmd "$PYTHON_BIN"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
else
  echo "Missing $ENV_FILE. Cannot continue." >&2
  exit 1
fi

: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:?DB_PORT is required}"
: "${DB_NAME:?DB_NAME is required}"
: "${DB_USER:?DB_USER is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"

mkdir -p "$TMP_DIR"

log "Dumping production database to $DUMP_FILE"
export PGPASSWORD="$DB_PASSWORD"
pg_dump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --no-owner \
  --no-privileges \
  --format=plain \
  --file="$DUMP_FILE"
unset PGPASSWORD

log "Dump complete: $(du -h "$DUMP_FILE" | awk '{print $1}')"

if [[ -f "$SQLITE_PATH" ]]; then
  confirm "Existing SQLite DB found at $SQLITE_PATH. Overwrite"
  rm -f "$SQLITE_PATH"
fi

export DJANGO_ENV="development"
log "Running migrations against SQLite schema"
"$PYTHON_BIN" "$MANAGE_PY" migrate --noinput

log "Loading production data into SQLite"
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/load_prod_into_sqlite.py" --dump "$DUMP_FILE" --sqlite "$SQLITE_PATH"

log "SQLite database refreshed at $SQLITE_PATH"
