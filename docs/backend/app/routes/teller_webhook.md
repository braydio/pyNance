# backend/app/routes Documentation

---

## 📘 `teller_transactions.py`

````markdown
# Teller Transactions Route

## Purpose

Exposes transaction data retrieved from the Teller API. Supports access to synced financial activity including filtering, syncing, and transaction lookup.

## Key Endpoints

- `GET /teller/transactions`: Retrieve list of synced transactions.
- `GET /teller/transactions/<id>`: Get a specific Teller transaction.
- `POST /teller/transactions/sync`: Force synchronization of latest data.

## Inputs & Outputs

- **GET /teller/transactions**
  - **Params:** `start_date`, `end_date`, `account_ids[]` (optional)
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

## 📘 `teller_webhook.py`

````markdown
# Teller Webhook Route

## Purpose

Processes webhook events sent by Teller, such as transaction updates, balance changes, or account status changes. Responsible for triggering backend sync jobs and refreshing relevant data.

## Key Endpoints

- `POST /teller/webhook`: Entry point for Teller webhook events.

## Inputs & Outputs

- **POST /teller/webhook**
  - **Input:** Webhook event body sent from Teller:
    ```json
    {
      "type": "transaction.created",
      "data": {
        "transaction_id": "txn_999",
        "account_id": "acct_001"
      }
    }
    ```
  - **Output:** `{ received: true }` or `{ error: "reason" }`

## Internal Dependencies

- `services.teller_webhook_service`
- `jobs.sync_transaction_job`
- `models.Transaction`, `models.WebhookLog`

## Known Behaviors

- Verifies signature or token for authenticity
- Idempotent handling of repeated webhook events
- Push-triggered ingestion pipeline for low-latency updates

## Related Docs

- [`docs/dataflow/teller_webhook.md`](../../dataflow/teller_webhook.md)
- [`docs/jobs/sync_transaction_job.md`](../../jobs/sync_transaction_job.md)
````

---

All `teller_*.py` routes now fully documented. Let me know when you're ready for the next module set.
