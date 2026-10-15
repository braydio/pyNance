# `plaid_liabilities`

Optional, Item-scoped Plaid Liabilities enrichment (TP-20261014-007).

- `refresh_item_liabilities(item_id, access_token, products=..., owner_user_id=...)` makes **one** `/liabilities/get` per Item and only when the Item's persisted scopes already include `liabilities`. It never enables the product or requests consent.
- `parse_liabilities` keeps card APR buckets separate (`purchase_apr`, `cash_apr`, `balance_transfer_apr`, `penalty_apr`, `special[]`), keeps loan/mortgage rates under `loan_interest_rate`, and ignores unknown product shapes.
- `apply_liabilities` writes `apr_details`, `minimum_payment_amount`, `next_payment_due_date`, `statement_balance`, `statement_date`, `liabilities_status` (`ok` | `no_rates_reported` | `unavailable` | `stale`) and `liabilities_as_of`. `Account.apr` is set (source `provider`) only when a card reports exactly one distinct purchase APR; an empty APR list is never a 0% rate. Response accounts not on the Item, or owned by a different user, are rejected.
- Provider/consent/network failures never raise: status becomes `unavailable` (never fetched) or `stale` (older data kept), and `ITEM_LOGIN_REQUIRED` is surfaced as `reauth` so the refresh orchestrator can mark the Item and aggregate the error.

The refresh orchestrators in `app/routes/accounts.py` call the adapter once per Item per refresh. `GET /api/accounts/get_accounts` adds `interest_rate_breakdown`, `rate_status`, `rate_source`, `rate_as_of`, `minimum_payment_amount`, `next_payment_due_date`, `statement_balance`, `statement_date`. These are cached provider values, not real-time.
