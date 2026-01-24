# backend/app/sql/dialect_utils.py

## Purpose

Expose dialect-aware SQLAlchemy INSERT helpers so callers can use conflict
handling on PostgreSQL and SQLite without branching on the database backend.

## Key Responsibilities

- Resolve the active SQLAlchemy dialect (defaulting to SQLite).
- Return a dialect-specific `insert` function when supported.

## Primary Functions

- `_current_dialect_name()`
  - Returns the active dialect name, defaulting to `sqlite` when unbound.
- `dialect_insert(table)`
  - Returns a PostgreSQL or SQLite insert with `on_conflict_do_*` support, or a
    generic insert fallback.

## Inputs

- SQLAlchemy table objects.

## Outputs

- SQLAlchemy insert statements (dialect-aware when possible).

## Internal Dependencies

- `app.extensions.db`
- `sqlalchemy.insert`

## Known Behaviors

- Defaults to SQLite when no bind is active (helpful for scripts/tests).
- Falls back to the generic insert for unsupported dialects.
