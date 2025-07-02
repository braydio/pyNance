# backend/app/sql Documentation

---

## Index of SQL Logic Modules

### 🧮 Transaction & Account Operations

- [`account_logic.py`](../../backend/app/sql/account_logic.py): SQL-level account resolution and user validation.
- [`transactions_logic.py`](../../backend/app/sql/transactions_logic.py): Transaction refresh helpers and pagination utilities.
- [`category_logic.py`](../../backend/app/sql/category_logic.py): Category inference, overrides, and bulk reclassification.

### 🔁 Recurring Logic

- [`recurring_logic.py`](../../backend/app/sql/recurring_logic.py): Match, link, and schedule recurring transaction sequences.

### 📈 Forecasting

- [`forecast_logic.py`](../../backend/app/sql/forecast_logic.py): Time-series generation for predictive engines.

### 📥 Import/Export

- [`manual_import_logic.py`](../../backend/app/sql/manual_import_logic.py): CSV parsing and ingestion of user-uploaded transaction data.
- [`export_logic.py`](../../backend/app/sql/export_logic.py): Structured export of balances and transactions.

---

## 📘 `transactions_logic.py`

```markdown
# Transactions Logic Module

Utility layer for pulling transactions from external providers and
exposing paginated query helpers.

## Primary Functions

- `fetch_url_with_backoff`
- `refresh_data_for_teller_account`
- `refresh_data_for_plaid_account`
- `get_paginated_transactions`
```

---

All core SQL logic modules documented. Ready to continue with `models/` layer?
