# transactions_logic.py

Provides helpers for pulling transactions from Plaid and Teller and for
paging through stored records. The module was split from
`account_logic.py` to keep account state management separate from
transaction synchronization. Key functions include:

- `fetch_url_with_backoff` – simple HTTP GET wrapper that retries with
  exponential backoff when a `429` is received.
- `refresh_data_for_teller_account` – updates balance and transaction
  history for a Teller account.
- `refresh_data_for_plaid_account` – same for Plaid-linked accounts.
- `get_paginated_transactions` – returns a page of combined transaction
  and account rows for API responses.

Routes now import these helpers from `app.sql.transactions_logic`.
