# 📨 Teller Transaction Sync

**Module:** `app.sql.account_logic.refresh_data_for_teller_account`
**Purpose:** Fetch balances and transactions from Teller and persist them.

---

## 🔄 Flow Overview

1. Tokens are loaded via `helpers.teller_helpers.load_tokens`.
2. For each account token, the service requests:
   - `GET /accounts/<id>/balances`
   - `GET /accounts/<id>/transactions`
   using the certificate pair in `backend/app/certs/`.
3. Balances update `Account.balance` and create an `AccountHistory` record for the current day.
4. Transactions are inserted or updated in the `Transaction` table. Records modified by users are preserved.
5. Called by refresh routes and the Teller webhook to keep data current.

## 🗄️ Storage Details

- **Balances:** stored on `Account` and mirrored in `AccountHistory`.
- **Transactions:** stored in `Transaction` with amount, date, description and merchant info.

This sync routine ensures the database reflects the latest Teller data.
