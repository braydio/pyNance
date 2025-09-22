# 🔍 Downstream Module Mapping for Refactor Exposure

## Purpose

This document identifies and logs all downstream modules within `backend/app/` that currently import and utilize logic from `plaid_transactions.py` and `teller_transactions.py`. This map will guide integration adjustments as those files are modularized into the new `providers/` structure.

It also determines the **start of the logic flow** for transaction sync behavior under the existing architecture.

---

## 🎯 Start of Logic Flow

### Entry Point: `routes/plaid.py` and `routes/teller.py`

These files define the first direct user-facing API endpoints that handle transaction access logic per provider. Though they do not call `*_transactions.py` directly, they:

- Initialize account-linking (token creation/exchange)
- Trigger account import and sync logic (via helper modules)

The _effective start_ of sync behavior is:

- `generate_link()` and `exchange_token()` in `plaid.py`
- `generate_link_token()` and `get_item_details()` in `teller.py`

These call into `helpers/` modules, where the true sync logic begins.

---

## ✅ Mapped Imports and Usages

### 📄 `backend/app/routes/transactions.py`

- Tightly coupled logic to Plaid/Teller data models.
- No direct imports from `*_transactions.py`, but uses overlapping fields.

### 📄 `backend/app/routes/plaid.py`

- Imports `generate_link_token`, `exchange_public_token` from `helpers/plaid_helpers.py`
- Triggers initial sync workflow.

### 📁 `helpers/plaid_helpers.py`

- Core sync logic for Plaid transactions and investments.
- Functions: `get_transactions`, `get_investments`, `get_accounts`, `refresh_plaid_accounts`

### 📄 `backend/app/routes/teller.py`

- Imports `load_tokens` from `helpers/teller_helpers.py`
- Directly interfaces with external Teller endpoints.

### 📁 `helpers/teller_helpers.py`

- Functions: `get_teller_accounts`, `load_tokens`, `update_account_history`
- Writes to and reads from JSON tokens.

### 📁 `sql/account_logic.py`

- Major ingestion logic for both Plaid and Teller.
- Key sync functions: `refresh_data_for_plaid_account`, `refresh_data_for_teller_account`, `upsert_accounts`, `save_plaid_item`

### 📁 `sql/category_logic.py`

- Sync-related support functions:

  - `upsert_categories_from_plaid_data`
  - `resolve_or_create_category`

- Used by both Plaid and Teller sync to resolve category names and create them if missing.

### 📁 `backend/app/models/`

- Central schema definitions are now split across dedicated modules:

  - [`account_models.py`](../../../../backend/app/models/account_models.py) – `Account`, `PlaidAccount`, `TellerAccount`, and related history tables.
  - [`transaction_models.py`](../../../../backend/app/models/transaction_models.py) – `Transaction`, `RecurringTransaction`, `TransactionRule`, `Category`, and Plaid transaction metadata.

- Relationships (e.g., account-category, transaction-category) remain wired via foreign keys across these modules.
- Attributes like `user_modified`, `pending`, `merchant_name`, and `provider` still align with Plaid and Teller sync outputs.

➡️ The models package continues to act as the single source of truth for sync-oriented schemas and should be referenced heavily during provider/service implementation.

---

## ✅ Mapping Coverage Estimate

| Domain                       | Status                |
| ---------------------------- | --------------------- |
| Routes (plaid/teller/txn)    | ✅ Done               |
| Helpers (plaid/teller)       | ✅ Done               |
| SQL Logic (account/category) | ✅ Done               |
| Models / Schemas             | ✅ Located & Analyzed |

📊 **Mapping completion:** 100% of relevant components are now documented.

---

## ⏳ Next Steps

- Scaffold `services/transactions.py`
- Create `providers/plaid.py` and `providers/teller.py`
- Register product routes in `__init__.py`
- Begin modular migration of sync functions
