# backend/app/sql/sequence_utils.py

## Purpose

Maintain database sequence health for transaction IDs when running on PostgreSQL.

## Key Responsibilities

- Sync the `transactions.id` sequence to the current max ID.
- Avoid touching non-PostgreSQL backends.

## Primary Functions

- `ensure_transactions_sequence()`
  - Calls `setval` on the `transactions.id` sequence using the current max ID.

## Inputs

- None (uses the active SQLAlchemy session bind).

## Outputs

- None; logs a warning if sequence synchronization fails.

## Internal Dependencies

- `sqlalchemy.text`
- `app.extensions.db`
- `app.config.logger`

## Known Behaviors

- No-op when the session bind is missing or not PostgreSQL.
- Uses `COALESCE(MAX(id), 0)` to handle empty tables safely.

## Related Docs

- `docs/backend/app/sql/index.md`
