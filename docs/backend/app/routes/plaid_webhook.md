# backend/app/routes Documentation

---

## 📘 `plaid_webhook.py`

````markdown
# Plaid Webhook Route

## Purpose

Validates Plaid webhook requests and dispatches downstream sync jobs for
transactions, investments, and holdings updates. Every request is authenticated
with Plaid's `Plaid-Signature` header before any payload processing occurs.

## Key Endpoints

- `POST /webhooks/plaid`: Primary entry point for Plaid webhook events. Expects
  signed JSON payloads matching Plaid's webhook schema.

## Inputs & Outputs

- **POST /webhooks/plaid**
  - **Input:** Plaid webhook payload, for example:
    ```json
    {
      "webhook_type": "TRANSACTIONS",
      "webhook_code": "DEFAULT_UPDATE",
      "item_id": "item-123"
    }
    ```
  - **Output:**
    - `{ "status": "ok", "triggered": [...] }` on success
    - `{ "status": "invalid_signature" }` when the signature fails validation
    - `{ "status": "error", "message": "Plaid webhook secret not configured." }`
      if the route is invoked without the required environment setup

## Internal Dependencies

- `models.PlaidWebhookLog` for storing incoming payload metadata
- `models.PlaidAccount` to resolve affected accounts for sync
- `services.plaid_sync.sync_account_transactions`
- `helpers.plaid_helpers.get_investment_transactions`
- `sql.investments_logic` helpers for investments + holdings updates

## Known Behaviors

- Rejects requests missing or failing the `Plaid-Signature` check with HTTP 400
- Logs every accepted webhook into `PlaidWebhookLog`
- Triggers targeted sync routines based on `webhook_type`/`webhook_code`
- Ignores payloads that do not include a Plaid `item_id`

## Setup

- Configure `PLAID_WEBHOOK_SECRET` in `backend/.env` (or environment) with the
  Plaid webhook signing secret so signature verification can succeed
- Ensure `BACKEND_PUBLIC_URL` is set when registering the webhook in Plaid so
  Plaid can reach `/api/webhooks/plaid`

## Related Docs

- [`docs/dataflow/plaid_ingestion_pipeline.md`](../../dataflow/plaid_ingestion_pipeline.md)
- [`docs/backend/app/sql/models/PlaidWebhookLog.md`](../sql/models/PlaidWebhookLog.md)
````

---

Plaid webhook documentation added.
