# Fix sequences after PostgreSQL data migration

This migration aligns auto-increment sequences with the current max primary keys to prevent duplicate key errors after bulk imports or manual data moves.

- Revision: `1f2a3b4c5d6e`
- Depends on: `4b9af1d3db6d`
- Source: `backend/migrations/versions/1f2a3b4c5d6e_fix_sequences_after_pg_migration.py`

Key points:

- Updates sequences/identity for `transactions(id)` and `plaid_transaction_meta(id)` to `MAX(id)`.
- Handles both legacy `SERIAL` and `IDENTITY` columns via catalog lookups.
- No-op on downgrade.

Why: without bumping sequences after importing data, inserts can fail with `psycopg.errors.UniqueViolation` on primary keys.

