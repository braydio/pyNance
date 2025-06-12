# 📣 Teller Webhook Processing

**Module:** `app.routes.teller_webhook`
**Purpose:** React to Teller events and trigger account refresh.

---

## 🔔 Workflow

1. `verify_signature` checks the `Teller-Signature` header using `TELLER_WEBHOOK_SECRET`.
2. Payload is parsed for `event` and `account_id`.
3. The matching `Account` and access token are looked up via `teller_helpers.load_tokens`.
4. `account_logic.refresh_data_for_teller_account` fetches the latest balances and transactions.
5. On success, `account.last_refreshed` is updated and a simple `{"status": "ok"}` is returned.

Webhook events keep Teller data in sync without manual intervention.
