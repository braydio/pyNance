# Add transaction tags

This migration adds a `tags` table and a `transaction_tags` association table to
support user-defined transaction labels.

- Revision: `55d16a2ff3e7`
- Depends on: `b1f9c2a6c57f`
- Source: `backend/migrations/versions/55d16a2ff3e7_add_transaction_tags.py`

Actions performed:

- Create `tags` with a per-user unique constraint on tag names and a user_id index.
- Create `transaction_tags` to associate `transactions.transaction_id` with `tags.id`.
- Add indexes on `transaction_tags.transaction_id` and `transaction_tags.tag_id`.

Notes:

- `get_paginated_transactions` in `backend/app/sql/account_logic.py` serializes
  tag names and defaults to `#untagged` when no tags are associated.
