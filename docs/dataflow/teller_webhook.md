# 📢 Teller Webhook Processing

This document outlines how incoming Teller webhook events are handled.

## Processing Steps

1. Webhooks arrive at `/api/webhooks/teller`.
2. `teller_webhook.py` verifies the `Teller-Signature` header using `TELLER_WEBHOOK_SECRET`.
3. The account is looked up and its stored access token is loaded.
4. `refresh_data_for_teller_account` is invoked to pull the latest balances and transactions.
5. If updates are made, the account's `last_refreshed` timestamp is saved.

Unsupported events return a simple OK response so Teller considers them delivered.

## Key Modules

- `backend/app/routes/teller_webhook.py`
- `backend/app/sql/account_logic.py`
- `backend/app/helpers/teller_helpers.py`
