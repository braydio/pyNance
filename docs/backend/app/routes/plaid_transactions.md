# backend/app/routes Documentation

---

## 📘 `plaid_transactions.py`

````markdown
# Plaid Transactions Route

## Purpose

Synchronizes and exposes transaction data retrieved via the Plaid API. Allows users to fetch, review, and interact with their financial transactions pulled from linked institutions.

## Key Endpoints

- `GET /plaid/transactions`: Retrieve all synced transactions.
- `GET /plaid/transactions/<id>`: Fetch a specific transaction by its ID.
- `POST /plaid/transactions/sync`: Force-refresh Plaid transactions for the user.
- `POST /plaid/transactions/refresh_accounts`: Refresh Plaid accounts and transactions.

## Inputs & Outputs

- **GET /plaid/transactions**

  - **Params (optional):**
    - `start_date`, `end_date`
    - `account_ids[]`
  - **Output:**
    ```json
    [
      {
        "id": "txn_001",
        "date": "2024-11-18",
        "amount": -64.23,
        "name": "Target",
        "category": "Shopping"
      }
    ]
    ```

- **GET /plaid/transactions/<id>**

  - **Output:** Transaction object with full metadata

- **POST /plaid/transactions/sync**
  - **Output:** `{ success: true, new_records: int }`

- **POST /plaid/transactions/refresh_accounts**
  - **Body:** `{ "user_id": "abc", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "account_ids": ["id1"] }`
  - **Output:** `{ "status": "success", "updated_accounts": ["name"] }`

## Internal Dependencies

- `services.plaid_transaction_service`
- `models.Transaction`
- `utils.date_filtering`, `auth.user_context`

## Known Behaviors

- Automatically paginates Plaid’s transactions API
- Categorization applied post-ingestion
- Partial deduplication across manual and synced data

## Related Docs

- [`docs/dataflow/transaction_sync.md`](../../dataflow/transaction_sync.md)
- [`docs/models/Transaction.md`](../../models/Transaction.md)
````

---

Next: `plaid_transfer.py`?
