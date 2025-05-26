## 📁 Component: `routes/teller_transactions.py`

### ✅ Exposed Functions (Impacted by Refactor)

These contain Teller-specific sync logic and will be refactored into:
`providers/teller.py`

- `teller_refresh_accounts()`

  - Syncs stored Teller tokens and updates account/transaction data.

- `teller_get_transactions()`

  - Returns paginated stored transaction data.

- `refresh_balances()`

  - Updates historical balance snapshots per Teller account.

- `update_transaction()`

  - Updates a single editable transaction field.

- `delete_teller_account()`

  - Removes a Teller account and related records from DB.

### ⚠️ Partial Exposure

- `teller_refresh_accounts()`

  - Also modifies local accounts and categories; split required between service/provider.

- `teller_get_transactions()`

  - Exposes pagination logic (likely reusable via service layer).

### 🚫 Non-Exposed / Ancillary Functions

- `save_teller_token()`

  - Token persistence not required in provider layer.

- `teller_exchange_public_token()`

  - Not required for `sync` calls (but may belong to auth route).

- `get_accounts()`

  - General data listing logic; may stay in product-facing routes.

---
