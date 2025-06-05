| Function                   | Purpose                                 | Likely Destination                   |
| -------------------------- | --------------------------------------- | ------------------------------------ |
| `get_transactions()`       | Calls Plaid `/transactions/get`         | `providers/plaid.py`                 |
| `get_investments()`        | Calls Plaid `/investments/holdings/get` | `providers/plaid.py`                 |
| `get_accounts()`           | Fetches and stores accounts from Plaid  | `providers/plaid.py`                 |
| `exchange_public_token()`  | Handles public → access token exchange  | May stay in auth service or move     |
| `generate_link_token()`    | Initiates a new link token              | May stay in route or auth service    |
| `refresh_plaid_accounts()` | Refreshes stored accounts               | Needs split between provider/service |
| `sync_plaid_transactions()` | Persists transaction updates            | `services/transactions.py` |
