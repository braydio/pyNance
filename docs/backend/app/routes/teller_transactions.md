backend/app/routes Documentation

---

## 📘 `teller_transactions.py`

````markdown
# Teller Transactions Route

## Purpose

Exposes transaction data retrieved from the Teller API. Supports user access to synced financial activity including filtering, syncing, and transaction lookup.

## Key Endpoints

- `GET /teller/transactions`: Retrieve list of synced transactions.
- `GET /teller/transactions/<id>`: Get a specific Teller transaction.
- `POST /teller/transactions/sync`: Force synchronization of latest data.

## Inputs & Outputs

- **GET /teller/transactions**

  - **Params:** `start_date`, `end_date`, `category`, `account_ids[]` (optional)
  - **Output:**
    ```json
    [
      {
        "id": "txn_042",
        "date": "2024-11-12",
        "description": "Starbucks",
        "amount": -4.75,
        "category": "Coffee"
      }
    ]
    ```

- **GET /teller/transactions/<id>`**

  - **Output:** Full transaction metadata (institution ID, type, raw payload)

- **POST /teller/transactions/sync**
  - **Output:** `{ success: true, imported_count: int }`

## Internal Dependencies

- `services.teller_transaction_service`
- `models.Transaction`
- Token + session context validation

## Known Behaviors

- Includes Plaid-style normalized output
- New transactions trigger enrichment and categorization
- May fallback to raw Teller data if enrichment fails

## Related Docs

- [`docs/dataflow/teller_transaction_sync.md`](../../dataflow/teller_transaction_sync.md)
- [`docs/models/Transaction.md`](../../models/Transaction.md)
````

---

Next: `teller_webhook.py`?
