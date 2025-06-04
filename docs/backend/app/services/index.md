# backend/app/services Documentation

---

## Index of Service Modules

### Forecasting

- [`forecast_balance.py`](#forecast-balance-service): Daily cashflow and forward balance projections.
- [`forecast_engine.py`](#forecast-engine-service): Core system for predictive modeling and spending estimation.
- [`forecast_orchestrator.py`](#forecast-orchestrator-service): High-level integration and coordination of forecasting components.
- [`forecast_stat_model.py`](#forecast-statistical-model-service): Statistical regressions for category forecasting.

### Recurring Transactions

- [`recurring_bridge.py`](#recurring-bridge-service): Synchronization layer between new transactions and recurrence tracking.
- [`recurring_detection.py`](#recurring-detection-service): Pattern mining to infer recurring flows.

### Synchronization & Storage

- [`sync_service.py`](#sync-service): Orchestrates transaction ingestion from APIs or files.
- [`transactions.py`](#transactions-service): Core logic for interacting with transaction data.

---

## 📘 `transactions.py`

```markdown
# Transactions Service

## Purpose

Provides core logic for managing user transactions. Supports listing, filtering, inserting, editing, and tagging financial records. Serves as the business logic layer beneath `/transactions` API endpoints.

## Key Responsibilities

- Abstract access to transaction models
- Apply user-scope filters and ownership logic
- Normalize imported transactions into internal schema
- Maintain data consistency across manual and synced entries

## Primary Functions

- `get_transactions(user_id, filters)`

  - Returns a filtered list of transactions for the user

- `create_transaction(user_id, data)`

  - Inserts a new user-defined transaction (manual or imported)

- `update_transaction(transaction_id, updates)`

  - Modifies editable fields like category, description

- `delete_transaction(transaction_id)`
  - Removes a user-created transaction

## Inputs

- Filter criteria: `date_range`, `account`, `merchant`, `tags`, `source`
- `user_id` from session context
- New or updated transaction data

## Outputs

- `Transaction` objects
- Validation errors or success messages
- Derived metadata for UI (e.g., summaries)

## Internal Dependencies

- `models.Transaction`
- `utils.transaction_filters`, `utils.transaction_normalizer`
- Tag parser, category reclassifier

## Known Behaviors

- Auto-tags certain descriptions (e.g., "Uber" → Travel)
- Prevents edits to externally-synced records unless flagged editable
- Emits signals/hooks for budget & summary recomputation

## Related Docs

- [`docs/models/Transaction.md`](../../models/Transaction.md)
- [`docs/dataflow/transaction_lifecycle.md`](../../dataflow/transaction_lifecycle.md)
```

---

All service files now documented. Ready for `db_logic/` layer next?
