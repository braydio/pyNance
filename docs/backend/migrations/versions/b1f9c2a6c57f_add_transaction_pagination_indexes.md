# Add transaction pagination indexes

This migration introduces composite indexes that mirror the filters and ordering used by transaction pagination and count queries.

- Revision: `b1f9c2a6c57f`
- Depends on: `f3d2c4a1b6e7`
- Source: `backend/migrations/versions/b1f9c2a6c57f_add_transaction_pagination_indexes.py`

Actions performed:

- Add a user-scoped index on `(user_id, date DESC, transaction_id DESC)` to support pagination ordered by posting date and tie-breaker.
- Add an account-scoped index on `(account_id, date DESC, transaction_id DESC)` to speed up ordered page fetches per account.
- Add an account/date index on `(account_id, date)` to accelerate range filters and counts when ordering is stripped for aggregates.

Notes:

- These indexes align with `get_paginated_transactions` in `backend/app/sql/account_logic.py`, ensuring both page queries and count operations rely on covering indexes.
