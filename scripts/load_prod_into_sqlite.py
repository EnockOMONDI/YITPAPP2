#!/usr/bin/env python3
"""Utility to hydrate the local SQLite database from production PostgreSQL data.

The script expects the PostgreSQL credentials to be available via the standard
DB_* environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD).
It verifies that a pg_dump artifact exists (so we always keep a raw snapshot),
and then streams data table-by-table into SQLite using psycopg2 + sqlite3.
"""
from __future__ import annotations

import argparse
import datetime as dt
import decimal
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import psycopg2
from psycopg2 import extras
from psycopg2 import sql

SUPPORTED_SIMPLE_TYPES = {
    'smallint', 'integer', 'bigint', 'numeric', 'real', 'double precision',
    'character varying', 'varchar', 'character', 'text', 'boolean', 'date',
    'timestamp without time zone', 'timestamp with time zone', 'json', 'jsonb',
    'uuid', 'bytea', 'ARRAY'
}

BIGINT_MAX = 2 ** 63 - 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Load production data into SQLite.')
    parser.add_argument('--dump', required=True, help='Path to the pg_dump file (for verification).')
    parser.add_argument('--sqlite', required=True, help='Path to the SQLite database file to populate.')
    parser.add_argument('--chunk-size', type=int, default=1000, help='Chunk size for streaming rows.')
    return parser.parse_args()


def ensure_dump_exists(dump_path: Path) -> None:
    if not dump_path.exists():
        raise FileNotFoundError(f'pg_dump file not found at {dump_path}')
    if dump_path.stat().st_size == 0:
        raise RuntimeError(f'pg_dump file at {dump_path} appears to be empty.')


def load_env_credentials() -> Dict[str, str]:
    required = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise EnvironmentError(f'Missing required DB credentials: {", ".join(missing)}')
    return {key: os.environ[key] for key in required}


def connect_postgres(creds: Dict[str, str]):
    connection = psycopg2.connect(
        host=creds['DB_HOST'],
        port=creds['DB_PORT'],
        dbname=creds['DB_NAME'],
        user=creds['DB_USER'],
        password=creds['DB_PASSWORD'],
        sslmode=os.environ.get('DB_SSLMODE', 'require'),
        connect_timeout=30,
    )
    connection.autocommit = False
    return connection


def connect_sqlite(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_sqlite_tables(sqlite_conn: sqlite3.Connection) -> List[str]:
    cursor = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def fetch_postgres_columns(pg_conn, tables: Sequence[str]) -> Dict[str, List[Tuple[str, str]]]:
    query = sql.SQL(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = ANY(%s)
        ORDER BY table_name, ordinal_position
        """
    )
    with pg_conn.cursor() as cur:
        cur.execute(query, (list(tables),))
        mapping: Dict[str, List[Tuple[str, str]]] = {}
        for table_name, column_name, data_type in cur.fetchall():
            mapping.setdefault(table_name, []).append((column_name, data_type))
        return mapping


def warn_on_unsupported_types(columns: Dict[str, List[Tuple[str, str]]]) -> None:
    for table, cols in columns.items():
        for column, data_type in cols:
            if data_type == 'ARRAY':
                print(f"[warning] Column {table}.{column} is an ARRAY. It will be serialized as JSON for SQLite.")
            elif data_type not in SUPPORTED_SIMPLE_TYPES:
                print(f"[warning] Column {table}.{column} uses unsupported type '{data_type}'. Attempting JSON fallback.")
            if data_type == 'bigint':
                print(f"[notice] Column {table}.{column} uses bigint. Verifying values stay within SQLite range.")


def warn_on_constraints(pg_conn) -> None:
    query = """
        SELECT conrelid::regclass::text AS table_name, conname, contype
        FROM pg_constraint
        WHERE connamespace = 'public'::regnamespace
    """
    with pg_conn.cursor() as cur:
        cur.execute(query)
        for table_name, conname, contype in cur.fetchall():
            if contype == 'x':
                print(f"[warning] Exclusion constraint {conname} on {table_name} is not enforced in SQLite.")
            elif contype == 'c':
                print(f"[notice] CHECK constraint {conname} on {table_name} may not be fully enforced in SQLite.")


def warn_on_sequences(pg_conn) -> None:
    query = """
        SELECT sequence_name, data_type
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    """
    with pg_conn.cursor() as cur:
        cur.execute(query)
        for sequence_name, data_type in cur.fetchall():
            if data_type == 'bigint':
                print(f"[notice] Sequence {sequence_name} uses bigint. SQLite AUTOINCREMENT uses signed 64-bit integers.")


def normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        if isinstance(value, dt.datetime) and value.tzinfo is not None:
            value = value.astimezone(dt.timezone.utc)
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return json.dumps(value)
    if isinstance(value, dict):
        return json.dumps(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return sqlite3.Binary(value)
    if isinstance(value, memoryview):
        return sqlite3.Binary(value.tobytes())
    return value


def stream_table(pg_conn, table: str, columns: Sequence[str], chunk_size: int):
    named_cursor = pg_conn.cursor(name=f'stream_{table}')
    try:
        named_cursor.itersize = chunk_size
        named_cursor.execute(
            sql.SQL('SELECT {} FROM {}').format(
                sql.SQL(', ').join(sql.Identifier(col) for col in columns),
                sql.Identifier('public', table)
            )
        )
        while True:
            rows = named_cursor.fetchmany(chunk_size)
            if not rows:
                break
            yield rows
    finally:
        named_cursor.close()


def delete_table(sqlite_conn: sqlite3.Connection, table: str) -> None:
    sqlite_conn.execute(f'DELETE FROM "{table}";')


def insert_rows(
    sqlite_conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[Any]],
    column_types: Dict[str, str]
) -> int:
    placeholder = ', '.join(['?'] * len(columns))
    column_list = ', '.join(f'"{col}"' for col in columns)
    sql_stmt = f'INSERT INTO "{table}" ({column_list}) VALUES ({placeholder})'

    processed_rows = []
    for row in rows:
        normalized = []
        for idx, value in enumerate(row):
            column = columns[idx]
            sqlite_type = column_types.get(column, '')
            converted = normalize_value(value)
            if isinstance(converted, int) and 'bigint' in sqlite_type.lower():
                if abs(converted) > BIGINT_MAX:
                    print(f"[warning] Value in {table}.{column} exceeds SQLite bigint range: {converted}")
            normalized.append(converted)
        processed_rows.append(tuple(normalized))

    if processed_rows:
        sqlite_conn.executemany(sql_stmt, processed_rows)
    return len(processed_rows)


def load_column_types(sqlite_conn: sqlite3.Connection, tables: Sequence[str]) -> Dict[str, Dict[str, str]]:
    table_map: Dict[str, Dict[str, str]] = {}
    for table in tables:
        cursor = sqlite_conn.execute(f'PRAGMA table_info("{table}")')
        table_map[table] = {row['name']: row['type'] for row in cursor.fetchall()}
    return table_map


def copy_tables(pg_conn, sqlite_conn, tables: Sequence[str], chunk_size: int) -> None:
    column_types_map = load_column_types(sqlite_conn, tables)
    pg_columns_map = fetch_postgres_columns(pg_conn, tables)
    warn_on_unsupported_types(pg_columns_map)
    warn_on_constraints(pg_conn)
    warn_on_sequences(pg_conn)

    sqlite_conn.execute('PRAGMA foreign_keys = OFF;')
    sqlite_conn.execute('BEGIN;')

    try:
        for table in tables:
            columns_data = pg_columns_map.get(table)
            if not columns_data:
                print(f"[skip] Table '{table}' not present in production database.")
                continue
            columns = [col for col, _ in columns_data]
            print(f"[table] Syncing {table} ({len(columns)} columns)...")
            delete_table(sqlite_conn, table)
            total_inserted = 0
            for chunk in stream_table(pg_conn, table, columns, chunk_size):
                total_inserted += insert_rows(
                    sqlite_conn,
                    table,
                    columns,
                    chunk,
                    column_types_map.get(table, {})
                )
            print(f"[table] Inserted {total_inserted} rows into {table}.")
    except Exception:
        sqlite_conn.rollback()
        raise
    else:
        sqlite_conn.commit()
    finally:
        sqlite_conn.execute('PRAGMA foreign_keys = ON;')


def main() -> None:
    args = parse_args()
    dump_path = Path(args.dump)
    sqlite_path = Path(args.sqlite)

    ensure_dump_exists(dump_path)
    creds = load_env_credentials()

    extras.register_default_json(loads=json.loads)
    extras.register_default_jsonb(loads=json.loads)

    pg_conn = connect_postgres(creds)
    sqlite_conn = connect_sqlite(sqlite_path)

    try:
        tables = get_sqlite_tables(sqlite_conn)
        if not tables:
            raise RuntimeError('No tables found in SQLite schema. Did migrations run?')
        copy_tables(pg_conn, sqlite_conn, tables, args.chunk_size)
        print('\n✅ SQLite database is now populated with production data.')
    finally:
        pg_conn.close()
        sqlite_conn.close()


if __name__ == '__main__':
    main()
