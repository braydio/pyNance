# Plaid Webhook Route (`plaid_webhook.py`)

## Purpose
Validate Plaid webhook requests and dispatch downstream sync jobs for transactions, investments, and holdings after signature verification.

## Endpoints
- `POST /webhooks/plaid` – Primary entry point for Plaid webhook events with signed JSON payloads.

## Inputs/Outputs
- **POST /webhooks/plaid**
  - **Inputs:** Plaid webhook payload (e.g., `{ "webhook_type": "TRANSACTIONS", "webhook_code": "DEFAULT_UPDATE", "item_id": "item-123" }`) with `Plaid-Signature` header.
  - **Outputs:**
    - `{ "status": "ok", "triggered": [...] }` on success.
    - `{ "status": "invalid_signature" }` when signature verification fails.
    - `{ "status": "error", "message": "Plaid webhook secret not configured." }` when environment is missing configuration.

## Auth
- Uses Plaid's signature verification; requests missing or failing the `Plaid-Signature` check return HTTP 400.

## Dependencies
- `models.PlaidWebhookLog` for logging incoming payloads.
- `models.PlaidAccount` to resolve affected accounts.
- `services.plaid_sync.sync_account_transactions` and investment helpers for targeted syncs.

## Behaviors/Edge Cases
- Ignores payloads without `item_id`.
- Logs every accepted webhook before invoking sync routines.
- Dispatches sync routines based on `webhook_type`/`webhook_code` combinations.

## Sample Request/Response
```http
POST /webhooks/plaid HTTP/1.1
Plaid-Signature: t=...,v1=...
Content-Type: application/json

{ "webhook_type": "TRANSACTIONS", "webhook_code": "DEFAULT_UPDATE", "item_id": "item-123" }
```

```json
{ "status": "ok", "triggered": ["transactions_sync"] }
```
