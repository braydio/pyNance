# backend/app/routes Documentation

---

## 📘 `plaid_transactions.py`

````markdown
# Plaid Transactions Route

## Purpose

Synchronizes and exposes transaction data retrieved via the Plaid API. Allows fetching, reviewing, and interacting with financial transactions pulled from linked institutions.

## Key Endpoints

- `GET /plaid/transactions`: Retrieve all synced transactions.
- `GET /plaid/transactions/<id>`: Fetch a specific transaction by its ID.
- `POST /plaid/transactions/sync`: Force-refresh Plaid transactions.

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

## Internal Dependencies

- `services.plaid_transaction_service`
- `models.Transaction`
- `utils.date_filtering`

## Known Behaviors

- Automatically paginates Plaid’s transactions API
- Categorization applied post-ingestion
- Partial deduplication across manual and synced data

## Related Docs

- [`docs/dataflow/transaction_sync.md`](../../dataflow/transaction_sync.md)
- [`docs/models/Transaction.md`](../../models/Transaction.md)
````

---

## 📘 `plaid_transfer.py`

````markdown
# Plaid Transfer Route

## Purpose

Enables money movement through linked Plaid-enabled bank accounts. Supports initiating transfers, tracking statuses, and viewing transfer history.

## Key Endpoints

- `POST /plaid/transfer/initiate`: Starts a new bank transfer.
- `GET /plaid/transfer/status/<transfer_id>`: Fetch status of a specific transfer.
- `GET /plaid/transfer/history`: List all past transfer attempts.

## Inputs & Outputs

- **POST /plaid/transfer/initiate**

  - **Input:**
    ```json
    {
      "amount": 150.0,
      "destination_account_id": "plaid_002",
      "description": "Rent payment"
    }
    ```
  - **Output:** `{ transfer_id: "trf_123", status: "pending" }`

- **GET /plaid/transfer/status/<transfer_id>`**

  - **Output:**
    ```json
    {
      "status": "completed",
      "settled_at": "2024-11-20T10:30:00Z"
    }
    ```

- **GET /plaid/transfer/history**
  - **Output:** Array of transfer metadata

## Internal Dependencies

- `services.transfer_service`
- `plaid.TransferClient`
- `models.Transfer`

## Known Behaviors

- Follows Plaid’s sandbox/live transfer APIs
- Handles idempotent submission to prevent duplicates
- Alerts if account not eligible for transfers

## Related Docs

- [`docs/dataflow/transfer_pipeline.md`](../../dataflow/transfer_pipeline.md)
- [`docs/models/Transfer.md`](../../models/Transfer.md)
````
