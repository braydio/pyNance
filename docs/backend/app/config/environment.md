## 📘 `environment.py`

```markdown
# Environment Variables

Loads `.env` values using `python-dotenv`. Defines keys for Plaid and Teller,
application mode (`FLASK_ENV`), and other runtime settings. This module centralizes
all environment lookups so the rest of the code can import settings directly.

### Key Variables

- `PRODUCTS` – comma-separated list of Plaid products enabled for linking.
  Defaults to `"transactions"` when unset. Values are consumed as a Python list
  in `environment.py` via `os.getenv("PRODUCTS", "transactions").split(",")`.
- `PLAID_ENV` – target Plaid environment (`sandbox`, `development`, `production`).
- `CLIENT_NAME` – display name passed to Plaid Link.
- `ENABLE_ARBIT_DASHBOARD` – set to `true` to expose the experimental arbitrage dashboard.

Specify multiple products (e.g., `transactions,investments`) to generate Link
tokens that cover more than one product. Each product still needs a separate
token exchange on the backend to persist its credentials.
```
