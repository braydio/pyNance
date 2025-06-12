# 📈 Teller Transaction Sync

Describes how Teller transactions are retrieved and stored.

## Flow Overview

1. Routes in `teller_transactions.py` call `account_logic.refresh_data_for_teller_account`.
2. `refresh_data_for_teller_account` uses `fetch_url_with_backoff` to request account balances and `/transactions` from the Teller API using the stored certificate pair and access token.
3. Each returned transaction is inserted or updated in the `Transaction` table. User-modified fields are preserved.
4. The latest balance for the account is recorded in both `Account` and `AccountHistory` tables.

Raw responses may be dumped to a temporary file for inspection during debugging.

## Key Modules

- `backend/app/sql/account_logic.py`
- `backend/app/routes/teller_transactions.py`
- `backend/app/helpers/teller_helpers.py`

These components coordinate to maintain an up‑to‑date ledger of Teller activity.
