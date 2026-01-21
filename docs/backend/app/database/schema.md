# Database Schema Utilities

## app/database/schema.py

Purpose

- Provides a single helper to create a non-public schema for development and test runs.

Behavior

- `ensure_schema(engine, schema)` opens a transaction and executes `CREATE SCHEMA IF NOT EXISTS <schema>`.
- Raises a `RuntimeError` if `schema == "public"` to prevent accidental changes to the default schema.
- Relies on `DB_SCHEMA` from `app.config.environment`, which is sourced from the `DB_SCHEMA` environment variable.

Call Site

- Invoked from the Flask application factory in `app/__init__.py` only when `IS_DEV` or `IS_TEST` is true.
- Runs inside an app context after `db.init_app(app)` so the engine is available.

Usage Notes

- This helper does not run at import time; it is a safe utility that requires an explicit call.
- The caller is responsible for providing the SQLAlchemy engine and a validated schema name.
- The guard intentionally blocks `public` so development and test work happens in isolated schemas.
