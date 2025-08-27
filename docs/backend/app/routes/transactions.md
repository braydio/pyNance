## 📘 `transactions.py`

````markdown
# Transactions Route

## Purpose

Provides a unified API surface for managing all transactions, including manually added, imported, and third-party (Plaid/Teller) data. Supports filtering, annotation, tagging, and CRUD operations.

## Key Endpoints

- `GET /transactions`: Retrieve list of all transactions.
- `GET /transactions/<id>`: Fetch metadata for a specific transaction.
- `POST /transactions`: Manually create a new transaction.
- `PATCH /transactions/<id>`: Update transaction fields.
- `DELETE /transactions/<id>`: Remove a transaction (usually manual-only).

## Inputs & Outputs

- **GET /transactions**

  - **Params:** Filters include `date_range`, `account_id`, `category`, `source`
  - **Output:** Array of transactions:
    ```json
    [
      {
        "id": "txn_987",
        "source": "plaid",
        "amount": -12.45,
        "merchant": "CVS",
        "category": "Pharmacy",
        "date": "2024-10-02"
      }
    ]
    ```

- **POST /transactions**

  - **Input:**
    ```json
    {
      "amount": 200,
      "date": "2024-12-01",
      "description": "Birthday gift",
      "category": "Gifts",
      "account_id": "acct_003"
    }
    ```
  - **Output:** Newly created transaction object

- **PATCH /transactions/<id>`**
  - **Input:** Partial updates for editable fields (e.g., `description`, `category`)

## Internal Dependencies

- `models.Transaction`
- `services.transaction_service`
- `utils.transaction_filters`

## Known Behaviors

- Read endpoints return normalized unified schema across data sources
- Edits may trigger re-evaluation of budgets and summaries

## Related Docs

- [`docs/models/Transaction.md`](../../models/Transaction.md)
- [`docs/dataflow/unified_transaction_model.md`](../../dataflow/unified_transaction_model.md)
````
