"""Helpers for working with SQLAlchemy dialect-specific features.

Provides runtime helpers to build INSERT statements that expose
``on_conflict_do_*`` methods for both SQLite and PostgreSQL so the rest of
the codebase can remain agnostic to the active database.
"""

from __future__ import annotations

from sqlalchemy import insert as generic_insert

from app.extensions import db


def _current_dialect_name() -> str:
    """Return the name of the bound SQLAlchemy dialect.

    Defaults to ``sqlite`` when no bind is active so that local scripts that
    run outside an application context continue to function.
    """

    try:
        bind = db.session.get_bind()  # type: ignore[arg-type]
    except RuntimeError:
        bind = None

    if bind is None:
        return "sqlite"

    return getattr(bind.dialect, "name", "sqlite")


def dialect_insert(table):
    """Return an INSERT statement tailored to the active database dialect."""

    dialect_name = _current_dialect_name()

    if dialect_name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        return pg_insert(table)

    if dialect_name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        return sqlite_insert(table)

    # Fallback to the generic insert which at least allows basic inserts even
    # if dialect-specific conflict resolution is unavailable.
    return generic_insert(table)
