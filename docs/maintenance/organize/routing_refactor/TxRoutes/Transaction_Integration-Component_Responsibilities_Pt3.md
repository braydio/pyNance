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

#### 🔗 Directly Exposed Functions (Used Internally)

- No direct imports from `plaid_transactions.py`.
- However, the logic inside this file reflects tightly coupled transaction handling that may be influenced or supplemented by Plaid data in practice.

#### 🛠️ Function Highlights

- `update_transaction()`
- `get_transactions_paginated()`
- `user_modified_update_transaction()`

These internally construct transaction update logic, refer to `Account`, and apply custom logic for:

- `amount`
- `date`
- `merchant_name`
- `category`
- `user_modified_fields`

➡️ These fields overlap with sync targets from Plaid.
➡️ This file should be audited post-refactor for redundant logic now handled in provider layer.

---

### 📄 `backend/app/routes/plaid.py`

#### 🔗 Imports:

```python
from app.helpers.plaid_helpers import generate_link_token, exchange_public_token
```

#### 🛠️ Function Highlights:

- `generate_link()` → uses `generate_link_token(user_id, products)`
- `exchange_token()` → uses `exchange_public_token(public_token)`

➡️ These are **indirectly related** to `plaid_transactions.py`, but source logic from helper modules.
➡️ No logic is imported directly from the core Plaid routes module.

---

## ⏳ Next Steps

- Review `app/helpers/` and `app/sql/` for overlap with transactions sync functions.
- Plan refactor path for helper-based logic into `providers/` where appropriate.
- Log additional references to transaction sync fields or behavior in shared logic modules.
