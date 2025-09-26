# backend/app/routes Documentation

---

## 📘 `teller_webhook.py`

````markdown
# Teller Webhook Route

## Purpose

Handle Teller webhook callbacks and reconcile account data when Teller
signals a change. Provides a disabled handler when webhook processing is
not configured.

## Key Endpoints

- `POST /api/webhooks/teller`
- `POST /api/webhooks/teller` _(disabled variant when no secret is set)_

## Inputs & Outputs

- **POST /api/webhooks/teller**
  - **Headers:** `Teller-Signature` HMAC SHA-256 signature
  - **Body:**
    ```json
    {
      "event": "transaction.posted",
      "data": { "account_id": "acct_123" }
    }
    ```
  - **Success:** `{ "status": "ok" }`
  - **Failures:**
    - `401` with `{ "status": "unauthorized" }` for missing/invalid signatures
    - `400` with `{ "status": "invalid" }` when payload lacks `event` or `account_id`

- **POST /api/webhooks/teller** _(disabled blueprint)_
  - **Output:** `{ "status": "disabled", "message": "Webhook is not enabled..." }`
  - Triggered when `TELLER_WEBHOOK_SECRET` is absent in configuration.

## Internal Dependencies

- `app.helpers.teller_helpers.load_tokens`
- `app.sql.account_logic.refresh_data_for_teller_account`
- `app.models.Account`
- `app.extensions.db`
- `FILES["TELLER_DOT_CERT"]` / `FILES["TELLER_DOT_KEY"]`

## Known Behaviors

- Uses `TELLER_WEBHOOK_SECRET` to verify signatures via HMAC + base64.
- Refreshes the affected account and updates `last_refreshed` timestamp
  when Teller reports posted or updated transactions.
- Logs and safely ignores webhook calls for unknown accounts or missing
  tokens.

## Related Docs

- [`docs/dataflow/teller_webhook.md`](../../dataflow/teller_webhook.md)
- [`docs/backend/app/routes/teller_transactions.md`](./teller_transactions.md)
````

---

All `teller_*.py` routes now reflect live code behavior.
