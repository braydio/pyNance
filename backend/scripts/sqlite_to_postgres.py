#!/usr/bin/env python3
"""Utility to copy data from the legacy SQLite database into PostgreSQL.

This script is now location-agnostic: it adjusts ``sys.path`` so that the
``backend/app`` package can be imported whether you run it from the repo root
or from ``backend/``. That means both invocations work:

    python backend/scripts/sqlite_to_postgres.py ...
    cd backend && python scripts/sqlite_to_postgres.py ...
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence

from sqlalchemy import MetaData, Table, create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

TABLE_SKIP = {"alembic_version"}
CHUNK_SIZE = 500


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite",
        required=True,
        help="Path to the legacy SQLite database file (dashboard_database.db).",
    )
    parser.add_argument(
        "--dsn",
        required=True,
        help="SQLAlchemy connection string for the PostgreSQL target.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help="Rows per insert batch (default: %(default)s).",
    )
    return parser.parse_args()


def chunked(rows: Iterable[dict], size: int) -> Iterable[Sequence[dict]]:
    buffer: list[dict] = []
    for row in rows:
        buffer.append(row)
        if len(buffer) >= size:
            yield tuple(buffer)
            buffer.clear()
    if buffer:
        yield tuple(buffer)


def stream_rows(sqlite_engine: Engine, table_name: str) -> Iterable[dict]:
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=sqlite_engine)
    with sqlite_engine.connect() as conn:
        result = conn.execution_options(stream_results=True).execute(select(table))
        for row in result:
            yield dict(row._mapping)


def insert_rows(pg_engine: Engine, table: Table, rows: Sequence[dict]) -> None:
    if not rows:
        return

    insert_stmt = table.insert()

    with pg_engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(insert_stmt, rows)
        except IntegrityError as exc:
            trans.rollback()
            print(
                f"Batch insert hit IntegrityError on {table.name}: {exc.orig}. Falling back to row-by-row."
            )
            for row in rows:
                nested = conn.begin()
                try:
                    conn.execute(insert_stmt.values(**row))
                    nested.commit()
                except IntegrityError as row_exc:
                    nested.rollback()
                    print(
                        f"  Skipping row in {table.name} due to IntegrityError: {row_exc.orig}"
                    )
            return
        else:
            trans.commit()


def postgres_has_rows(pg_engine: Engine, table: Table) -> bool:
    with pg_engine.connect() as conn:
        count = conn.execute(select(func.count()).select_from(table)).scalar_one()
    return count > 0


def copy_table(
    sqlite_engine: Engine, pg_engine: Engine, table: Table, chunk_size: int
) -> None:
    if table.name in TABLE_SKIP:
        return

    if postgres_has_rows(pg_engine, table):
        print(f"Skipping {table.name}: target already contains rows.")
        return

    print(f"Copying {table.name}...")
    row_iter = stream_rows(sqlite_engine, table.name)
    for batch in chunked(row_iter, chunk_size):
        insert_rows(pg_engine, table, batch)
    print(f"Finished {table.name}.")


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.sqlite):
        raise SystemExit(f"SQLite database not found: {args.sqlite}")

    # Ensure we can import the Flask app package regardless of CWD by adding
    # the backend directory (parent of this file's directory) to sys.path.
    this_file = Path(__file__).resolve()
    backend_dir = this_file.parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    sqlite_engine = create_engine(f"sqlite:///{args.sqlite}", future=True)
    pg_engine = create_engine(args.dsn, future=True)

    # Ensure metadata reflects the latest models.
    os.environ.setdefault("SQLALCHEMY_DATABASE_URI", args.dsn)
    from app import create_app
    from app.extensions import db

    app = create_app()

    with app.app_context():
        metadata = db.metadata
        for table in metadata.sorted_tables:
            copy_table(sqlite_engine, pg_engine, table, args.chunk_size)

    print(
        "Data migration complete. Run 'flask db upgrade' if additional migrations exist."
    )


if __name__ == "__main__":
    main()
