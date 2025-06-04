# backend/app/services Documentation

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

All service files now documented. Ready for summary, publishing, or moving to another layer?
