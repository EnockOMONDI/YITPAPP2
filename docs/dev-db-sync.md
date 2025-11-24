# Development Database Sync Guide

This workflow keeps local development in lockstep with production data while preserving the existing environment split (`DJANGO_ENV=development` vs `production`). The `scripts/sync_prod_to_sqlite.sh` helper performs every required step with a single, guarded command.

## Prerequisites
- `pg_dump`, `python3`, and `sqlite3` available in your shell.
- An up-to-date `.env` file with valid `DB_*` variables for production.
- Local `DJANGO_ENV` exported as `development` when running Django (`production` is untouched).
- Network access to the production database host.

## What the Script Does
1. Prompts for confirmation before touching production data or overwriting the local SQLite DB.
2. Sources `.env`, validates `DB_HOST/PORT/NAME/USER/PASSWORD`, and checks tooling.
3. Runs `pg_dump` to `tmp/sync_prod/prod_dump.sql` as an unmasked backup (kept out of Git by `.gitignore`).
4. Deletes any previous `db.dev.sqlite3` (after a second prompt) and runs `python manage.py migrate` so the SQLite schema matches HEAD.
5. Invokes `scripts/load_prod_into_sqlite.py` which:
   - Verifies the dump file exists for traceability.
   - Connects to production PostgreSQL using `psycopg2` and streams each table via server-side cursors.
   - Converts JSON/ARRAY columns to JSON text, serializes UUIDs, datetimes, decimals, booleans, and binary payloads into SQLite-friendly formats.
   - Disables SQLite foreign keys during bulk insert, re-enables afterwards, and warns about unsupported constraints or bigint auto-sequences.
6. Prints a success summary when the `db.dev.sqlite3` snapshot is ready for use.

## Usage
```bash
export DJANGO_ENV=development
./scripts/sync_prod_to_sqlite.sh
```
- Respond `yes` to both prompts to proceed.
- The script logs progress, table counts, and any warnings (e.g., exclusion constraints skipped, bigint values nearing limits).
- After completion you can run `python manage.py check` or your preferred test suite against the SQLite snapshot.

## Notes & Risks
- **PII**: This pulls full production data without masking, so treat `db.dev.sqlite3` and the dump file as sensitive.
- **Unsupported PostgreSQL features**: Exclusion and complex CHECK constraints are not enforced by SQLite; warnings call these out so you can add app-level guards if needed.
- **Big integers**: When values approach SQLite’s 64-bit ceiling the loader prints warnings; address these before inserts start failing.
- **Temp artifacts**: Dumps live under `tmp/sync_prod/` and are ignored by Git. Remove them manually if you no longer need them.

With this flow in place, the development environment always uses `db.dev.sqlite3`, while production keeps using PostgreSQL with no setting changes.
