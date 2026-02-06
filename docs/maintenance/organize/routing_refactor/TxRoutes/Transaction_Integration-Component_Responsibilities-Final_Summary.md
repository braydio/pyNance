# 🔍 Downstream Module Mapping for Refactor Exposure

## Purpose

This document identifies and logs all downstream modules within `backend/app/` that currently import and utilize logic from `plaid_transactions.py`. This map will guide integration adjustments as that file is modularized into the new `providers/` structure.

It also determines the **start of the logic flow** for transaction sync behavior under the existing architecture.

---

## 🎯 Start of Logic Flow

### Entry Point: `routes/plaid.py`

This file defines the first direct user-facing API endpoints that handle transaction access logic per provider. Though it does not call `plaid_transactions.py` directly, it:

- Initialize account-linking (token creation/exchange)
- Trigger account import and sync logic (via helper modules)

The _effective start_ of sync behavior is:

- `generate_link()` and `exchange_token()` in `plaid.py`

These call into `helpers/` modules, where the true sync logic begins.

---

## ✅ Mapped Imports and Usages

### 📄 `backend/app/routes/transactions.py`

- Tightly coupled logic to Plaid data models.
- No direct imports from `*_transactions.py`, but uses overlapping fields.

### 📄 `backend/app/routes/plaid.py`

- Imports `generate_link_token`, `exchange_public_token` from `helpers/plaid_helpers.py`
- Triggers initial sync workflow.

### 📁 `helpers/plaid_helpers.py`

- Core sync logic for Plaid transactions and investments.
- Functions: `get_transactions`, `get_investments`, `get_accounts`, `refresh_plaid_accounts`

### 📁 `sql/account_logic.py`

- Major ingestion logic for Plaid.
- Key sync functions: `refresh_data_for_plaid_account`, `upsert_accounts`, `save_plaid_item`

### 📁 `sql/category_logic.py`

- Sync-related support functions:
  - `upsert_categories_from_plaid_data`
  - `resolve_or_create_category`

- Used by Plaid sync to resolve category names and create them if missing.

### 📁 `backend/app/models/`

- Central schema definitions are now split across dedicated modules:
  - [`account_models.py`](../../../../backend/app/models/account_models.py) – `Account`, `PlaidAccount`, and related history tables.
  - [`transaction_models.py`](../../../../backend/app/models/transaction_models.py) – `Transaction`, `RecurringTransaction`, `TransactionRule`, `Category`, and Plaid transaction metadata.

- Relationships (e.g., account-category, transaction-category) remain wired via foreign keys across these modules.
- Attributes like `user_modified`, `pending`, `merchant_name`, and `provider` still align with Plaid sync outputs.

➡️ The models package continues to act as the single source of truth for sync-oriented schemas and should be referenced heavily during provider/service implementation.

---

## ✅ Mapping Coverage Estimate

| Domain                       | Status                |
| ---------------------------- | --------------------- |
| Routes (plaid/txn)           | ✅ Done               |
| Helpers (plaid)              | ✅ Done               |
| SQL Logic (account/category) | ✅ Done               |
| Models / Schemas             | ✅ Located & Analyzed |

📊 **Mapping completion:** 100% of relevant components are now documented.

---

## ⏳ Next Steps

- Scaffold `services/transactions.py`
- Create `providers/plaid.py`
- Register product routes in `__init__.py`
- Begin modular migration of sync functions
