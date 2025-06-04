# backend/app/db_logic Documentation

---

## Index of SQL Logic Modules

### 🧮 Transaction & Account Operations

- [`account_logic.py`](../../backend/app/db_logic/account_logic.py): SQL-level account resolution and user validation.
- [`transactions_logic.py`](../../backend/app/db_logic/transactions_logic.py): Filtering, batch updates, and transaction persistence.
- [`category_logic.py`](../../backend/app/db_logic/category_logic.py): Category inference, overrides, and bulk reclassification.

### 🔁 Recurring Logic

- [`recurring_logic.py`](../../backend/app/db_logic/recurring_logic.py): Match, link, and schedule recurring transaction sequences.

### 📈 Forecasting

- [`forecast_logic.py`](../../backend/app/db_logic/forecast_logic.py): Time-series generation for predictive engines.

### 📥 Import/Export

- [`manual_import_logic.py`](../../backend/app/db_logic/manual_import_logic.py): CSV parsing and ingestion of user-uploaded transaction data.
- [`export_logic.py`](../../backend/app/db_logic/export_logic.py): Structured export of balances and transactions.

---

## 📘 `transactions_logic.py`

```markdown
# Transactions Logic Module

## Purpose

Implements SQL-backed routines for managing transaction records. Handles inserts, updates, lookups, and rollups using direct SQL or ORM-based batch operations. Powers most of the backend workflows involving user transactions.

## Key Responsibilities

- Retrieve filtered transaction datasets
- Insert or update records atomically
- Support batch operations and scoped joins

## Primary Functions

- `get_user_transactions(user_id, filters)`

  - Applies WHERE clauses on account, date, category, etc.

- `insert_transaction(user_id, data)`

  - Commits a new transaction row with relational validation

- `bulk_update_categories(transaction_ids, category_id)`

  - Updates category for multiple transactions at once

- `delete_transaction(transaction_id)`
  - Marks a transaction deleted or removes it entirely

## Inputs

- `user_id`, filter parameters, payload dicts
- Transaction metadata: description, amount, date, tags

## Outputs

- Transaction records or summaries
- Count of affected rows for bulk ops
- Post-update signals (budget refresh, tag rebuild)

## Internal Dependencies

- `models.Transaction`, `models.Category`, `models.Account`
- SQLAlchemy query builders
- `utils.transaction_filters`

## Known Behaviors

- Inserts trigger post-hooks to forecast + recurring modules
- Date coercion applied automatically during insert
- Filter logic reused in `/transactions` route and dashboard exports

## Related Docs

- [`docs/dataflow/transaction_lifecycle.md`](../../dataflow/transaction_lifecycle.md)
- [`docs/frontend/pages/TransactionsPage.md`](../../frontend/pages/TransactionsPage.md)
```

---

All core SQL logic modules documented. Ready to continue with `models/` layer?
