
# ?? Downstream Module Mapping for Refactor Exposure

## Purpose

This document identifies and logs all downstream modules within `backend/app/` that currently import and utilize logic from `plaid_transactions.py` and `teller_transactions.py`. This map will guide integration adjustments as those files are modularized into the new `providers/` structure.

---

## ? Mapped Imports and Usages

### ?? `backend/app/routes/transactions.py`

#### ?? Directly Exposed Functions (Used Internally)

* No direct imports from `plaid_transactions.py` or `teller_transactions.py`.
* However, the logic inside this file reflects tightly coupled transaction handling that may be influenced or supplemented by Plaid/Teller data in practice.

#### ??? Function Highlights

* `update_transaction()`
* `get_transactions_paginated()`
* `user_modified_update_transaction()`

These internally construct transaction update logic, refer to `Account`, and apply custom logic for:

* `amount`
* `date`
* `merchant_name`
* `category`
* `user_modified_fields`

?? These fields overlap with sync targets from Plaid/Teller.
?? This file should be audited post-refactor for redundant logic now handled in provider layer.

---

### ?? `backend/app/routes/plaid.py`

#### ?? Imports:

```python
from app.helpers.plaid_helpers import generate_link_token, exchange_public_token
```

#### ??? Function Highlights:

* `generate_link()` ? uses `generate_link_token(user_id, products)`
* `exchange_token()` ? uses `exchange_public_token(public_token)`

?? These are **indirectly related** to `plaid_transactions.py`, but source logic from helper modules.
?? No logic is imported directly from the core Plaid routes module.

---

### ?? `backend/app/routes/teller.py`

#### ?? Imports:

```python
from app.helpers.teller_helpers import load_tokens
from app.db_logic.account_logic import get_accounts_from_db
```

#### ??? Function Highlights:

* `generate_link_token()` ? Calls external Teller API directly
* `get_item_details()`, `get_accounts()` ? Contain raw sync logic

?? All sync logic is **self-contained** or delegated to helpers.
?? `teller_transactions.py` is **not referenced**, though functionality overlaps.

---

## ? Next Steps

* Review `app/helpers/` and `app/db_logic/` for overlap with transactions sync functions.
* Plan refactor path for helper-based logic into `providers/` where appropriate.
* Log additional references to transaction sync fields or behavior in shared logic modules.
