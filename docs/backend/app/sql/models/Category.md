# 📘 `Category` Model

```markdown
# Category Model

## Purpose

Represents a labeled classification used to group transactions. Can be system-defined (e.g. "Groceries", "Utilities") or user-defined. Enables budget planning, filtering, and analytic aggregation.

## Fields

- `id`: Primary key (UUID or integer)
- `user_id`: Optional — null means global/shared category
- `name`: String label (e.g. "Dining Out")
- `parent_id`: Nullable FK to allow subcategory hierarchies
- `icon`: Optional emoji or glyph for UI
- `color`: Hex or theme color ID
- `is_default`: Boolean, used to prevent deletion of system categories
- `created_at`, `updated_at`: Audit timestamps

## Relationships

- One-to-many with `Transaction`
- May group into parent/child trees for nesting

## Behaviors

- Global categories are shared across users
- Custom categories can override the same name
- Used as a budget key when computing limits

## Related Logic

- [`category_logic.py`](../../backend/app/sql/category_logic.py)
- [`forecast_stat_model.py`](../../backend/app/services/forecast_stat_model.py)
- [`transactions_logic.py`](../../backend/app/sql/transactions_logic.py)

## Related Docs

- [`docs/dataflow/category_matching.md`](../../docs/dataflow/category_matching.md)
- [`docs/sql/CategoryQueryPatterns.md`](../../docs/sql/CategoryQueryPatterns.md)
```
