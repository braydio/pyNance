# backend/app/routes Documentation

---

## 📘 `teller_transactions.py`

````markdown
# Teller Transactions Route

## Purpose

Expose Teller-linked account utilities, including token management,
manual refresh flows, and transaction retrieval helpers used by the
frontend when Plaid coverage is unavailable.

## Key Endpoints

- `POST /api/teller/transactions/save_access_token`
- `POST /api/teller/transactions/refresh_accounts`
- `GET /api/teller/transactions/get_transactions`
- `GET /api/teller/transactions/list_teller_accounts`
- `POST /api/teller/transactions/refresh_balances`
- `PUT /api/teller/transactions/update`
- `DELETE /api/teller/transactions/delete_account`

> ℹ️ `POST /api/teller/transactions/exchange_public_token` exists only
> to warn callers that Teller bypasses Plaid-style public-token
> exchanges. It always returns an error instructing clients to call
> `save_access_token` instead.

## Inputs & Outputs

- **POST /api/teller/transactions/save_access_token**
  - **Body:** `{ "user_id": "uuid", "access_token": "teller-access-..." }`
  - **Output:** `{ "status": "success" }`

- **POST /api/teller/transactions/refresh_accounts**
  - **Body:** none (tokens loaded from disk)
  - **Output:**
    ```json
    {
      "status": "success",
      "message": "Teller account data refreshed",
      "updated_accounts": ["Checking", "Savings"]
    }
    ```

- **GET /api/teller/transactions/get_transactions**
  - **Params:** `page`, `page_size`, `start_date`, `end_date`, `category`
  - **Output:** `{ "status": "success", "data": { "transactions": [...], "total": 42 } }`

- **GET /api/teller/transactions/list_teller_accounts**
  - **Params:** none
  - **Output:** `{ "status": "success", "data": { "accounts": [...] } }`

- **POST /api/teller/transactions/refresh_balances**
  - **Body:** `{ "account_ids": ["acct_123"] }` (optional filter)
  - **Output:**
    ```json
    {
      "status": "success",
      "message": "Balances refreshed",
      "updated_accounts": [{ "account_name": "Checking" }]
    }
    ```

- **PUT /api/teller/transactions/update**
  - **Body:** Transaction fields to mutate (amount, date, description, category,
    merchant metadata)
  - **Output:** `{ "status": "success" }` or `{ "status": "success", "message": "No changes applied" }`

- **DELETE /api/teller/transactions/delete_account**
  - **Body:** `{ "account_id": "acct_123" }`
  - **Output:** `{ "status": "success", "message": "Account and related records deleted" }`

## Internal Dependencies

- `app.helpers.teller_helpers.load_tokens/save_tokens`
- `app.sql.account_logic.refresh_data_for_teller_account`
- `app.models.Account` / `app.models.Transaction`
- `app.extensions.db`

## Known Behaviors

- Persists Teller credentials in `TellerDotTokens.json` for CLI-friendly
  management.
- Refresh endpoints update `account.last_refreshed` timestamps when new
  data is fetched.
- Transaction update path tracks field-level edits so downstream rules
  can audit manual overrides.

## Related Docs

- [`docs/dataflow/teller_transaction_sync.md`](../../dataflow/teller_transaction_sync.md)
- [`docs/models/Transaction.md`](../../models/Transaction.md)
````

---

Next: `teller_webhook.py`
