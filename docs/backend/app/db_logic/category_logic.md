## 📘 `category_logic.py`

```markdown
# Category SQL Logic

## Purpose

Provides SQL-layer utilities for managing transaction categories. Handles mappings, reclassification rules, custom user categories, and tag inference.

## Key Responsibilities

- Map transaction descriptions to categories
- Handle custom overrides and category definitions
- Perform batch reclassification jobs

## Primary Functions

- `get_default_category(description)`

  - Infers base category from transaction description

- `apply_user_category_overrides(user_id, transaction_id)`

  - Applies manual overrides from user settings or admin panel

- `reclassify_all(user_id)`
  - Re-evaluates all transactions with updated logic

## Inputs

- Transaction metadata (description, merchant, amount)
- Optional user category rules

## Outputs

- Category names (string), category_id (foreign key)
- Logs of affected transaction updates (optional)

## Internal Dependencies

- `models.Category`, `models.Transaction`
- `utils.category_rules`, `db_session`

## Known Behaviors

- Includes built-in fallback matching for known vendors
- Supports one-to-many mappings via tag sets
- Allows bulk remapping during schema updates

## Related Docs

- [`docs/models/Category.md`](../../models/Category.md)
- [`docs/dataflow/category_matching.md`](../../dataflow/category_matching.md)
```

---

Ready for `export_logic.py`?
