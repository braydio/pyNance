# Plaid Transactions Route (`plaid_transactions.py`)

## Purpose
Synchronize and expose transaction data retrieved via the Plaid API, supporting fetches, detail lookups, and manual refreshes.

## Endpoints
- `GET /plaid/transactions` – Retrieve synced transactions with optional filters.
- `GET /plaid/transactions/<id>` – Fetch a specific transaction by ID.
- `POST /plaid/transactions/sync` – Force-refresh Plaid transactions.
- `POST /plaid/transactions/refresh_accounts` – Refresh Plaid accounts and transactions with optional date scoping.

## Inputs/Outputs
- **GET /plaid/transactions**
  - **Inputs:** Optional `start_date`, `end_date`, and `account_ids[]` query params.
  - **Outputs:** Array of transaction objects with dates, amounts, names, and categories.
- **GET /plaid/transactions/<id>**
  - **Inputs:** Path parameter `id`.
  - **Outputs:** Full transaction object.
- **POST /plaid/transactions/sync**
  - **Inputs:** None.
  - **Outputs:** `{ "success": true, "new_records": int }` summarizing ingest results.
- **POST /plaid/transactions/refresh_accounts**
  - **Inputs:** JSON body `{ "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "account_ids": ["id1"] }`.
  - **Outputs:** `{ "status": "success", "updated_accounts": ["name"] }` with refresh counts.

## Auth
- Requires authenticated user; transactions are scoped to linked Plaid items for that user.

## Dependencies
- `services.plaid_transaction_service` for sync logic.
- `models.Transaction` and date filtering utilities.

## Behaviors/Edge Cases
- Automatically paginates Plaid transactions and applies deduplication across manual/synced data.
- Categorization occurs post-ingestion.

## Sample Request/Response
```http
POST /plaid/transactions/refresh_accounts HTTP/1.1
Content-Type: application/json

{ "start_date": "2024-01-01", "end_date": "2024-01-15", "account_ids": ["acc_1"] }
```

```json
{ "status": "success", "updated_accounts": ["Checking"] }
```
