# Recent Transactions API

`GET /api/transactions/<account_id>/transactions?recent=true&limit=10`
returns the newest transactions for an account.

## Logic Overview
- `get_paginated_transactions` now accepts `account_id`, `recent`, and `limit` arguments.
- When `recent=true`, pagination is skipped and only the latest `limit` rows are returned.
- The new route wraps this logic and supports standard filtering params.

## Potential Issues
- Sorting relies on `Transaction.date` which may not match insertion time if data was backfilled.
