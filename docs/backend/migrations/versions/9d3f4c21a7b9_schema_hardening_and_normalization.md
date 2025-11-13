# Schema hardening and normalization

Revision `9d3f4c21a7b9` merges prior heads and tightens core schema:

- Moves `accounts` primary key to `account_id` and re-keys FKs.
- Casts `account_history.date` to `Date` for daily snapshots.
- Introduces enums for `accounts.status`, `accounts.link_type`, and `transactions.provider` (Plaid/manual only).
- Adds `plaid_accounts.plaid_item_id` with FK to `plaid_items`.
- Creates practical indexes for common queries.

Source: `backend/migrations/versions/9d3f4c21a7b9_schema_hardening_and_normalization.py`.

