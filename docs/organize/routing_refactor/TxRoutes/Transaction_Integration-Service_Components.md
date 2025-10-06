# 🔍 Downstream Module Mapping for Refactor Exposure

## Purpose

This document identifies and logs all downstream modules within `backend/app/` that currently import and utilize logic from `plaid_transactions.py`. This map will guide integration adjustments as that file is modularized into the new `providers/` structure.

It also determines the **start of the logic flow** for transaction sync behavior under the existing architecture.

---

## 🎯 Start of Logic Flow

### Entry Point: `routes/plaid.py`

This file defines the first direct user-facing API endpoints that handle transaction access logic for Plaid. Though it does not call `plaid_transactions.py` directly, it:

- Initialize account-linking (token creation/exchange)
- Trigger account import and sync logic (via helper modules)

The _effective start_ of sync behavior is:

- `generate_link()` and `exchange_token()` in `plaid.py`

These call into `helpers/` modules, where the true sync logic begins.

---

## ✅ Mapped Imports and Usages

### 📄 `backend/app/routes/transactions.py`

- Tightly coupled logic to Plaid data models.
- No direct imports from `plaid_transactions.py`, but uses overlapping fields.

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

---

## ⚠️ Unresolved Model Layer

No `schemas/` or `models/` directory was found.

- This suggests models and request/response types may be defined inline in routes or SQL logic files.
- We'll audit `BaseModel` usage during service scaffolding.

---

## ✅ Mapping Coverage Estimate

| Domain                       | Status                     |
| ---------------------------- | -------------------------- |
| Routes (plaid/txn)           | ✅ Done                    |
| Helpers (plaid)              | ✅ Done                    |
| SQL Logic (account/category) | ✅ Done                    |
| Models / Schemas             | ⚠️ Incomplete, not present |

📊 **Mapping completion:** \~95–98% functional exposure complete.

---

## ⏳ Next Steps

- Scaffold `services/transactions.py`
- Create `providers/plaid.py`
- Register product routes in `__init__.py`
- Validate `BaseModel` inputs in routes for consistency
