# 📘 `Transaction` Model

```markdown
# Transaction Model

## Purpose

Captures a single financial transaction made by a user. This can be a synced transaction from an external provider (Plaid, Teller) or a manual entry. All transaction analysis, budgeting, and forecasting originates from this data.

## Fields

- `id`: Primary key (UUID)
- `user_id`: Foreign key to the owning user
- `account_id`: Foreign key to `Account`
- `date`: Transaction date
- `amount`: Float (positive = inflow, negative = outflow)
- `description`: Merchant or label
- `category_id`: Optional FK to `Category`
- `tags`: Array of custom user tags
- `is_pending`: Boolean flag for provisional transactions
- `is_recurring`: Boolean if linked to a recurring pattern
- `provider_transaction_id`: External source ID
- `source`: Enum (`plaid`, `teller`, `manual`, etc.)
- `created_at`, `updated_at`: Audit timestamps

## Relationships

- Belongs to `Account`
- Optionally linked to `RecurringTransaction`
- Categorized via `Category` or tag sets

## Behaviors

- Immutable once verified unless explicitly editable
- Amounts stored in absolute form, but signed by inflow/outflow
- Auto-categorization is run on creation and update

## Related Logic

- [`transactions_logic.py`](../../backend/app/sql/transactions_logic.py)
- [`category_logic.py`](../../backend/app/sql/category_logic.py)
- [`recurring_bridge.py`](../../backend/app/services/recurring_bridge.py)

## Related Docs

- [`docs/dataflow/transaction_lifecycle.md`](../../docs/dataflow/transaction_lifecycle.md)
- [`docs/sql/TransactionQueryPatterns.md`](../../docs/sql/TransactionQueryPatterns.md)
```
