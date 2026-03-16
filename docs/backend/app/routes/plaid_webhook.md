---
Owner: Backend Team
Last Updated: 2026-03-15
Status: Active
---

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
- `app.sql.account_logic.canonicalize_plaid_products` to parse canonical comma-delimited product scopes.

## Behaviors/Edge Cases

- Ignores payloads without `item_id`.
- Logs every accepted webhook before invoking sync routines.
- Dispatches sync routines based on `webhook_type`/`webhook_code` combinations.
- `TRANSACTIONS` sync webhooks call `plaid_sync.sync_account_transactions(account_id)` for each matching account to honor item-level cursors while preserving per-account failure isolation and triggered-account reporting.
- `INVESTMENTS_TRANSACTIONS` and `HOLDINGS` webhooks resolve accounts by `item_id`, then filter to accounts whose parsed scopes include `investments` (including canonical mixed scopes like `"investments,transactions"`).

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
