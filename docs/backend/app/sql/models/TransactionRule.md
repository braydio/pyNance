# \U0001F4D6 `TransactionRule` Model

```markdown
# TransactionRule Model

## Purpose

Stores persistent mapping of match criteria to actions applied on transactions. Allows future imports to be auto-categorized or adjusted.

## Fields

- `id`: Primary key (UUID)
- `user_id`: Foreign key to `User`
- `match_criteria`: JSON document describing patterns (merchant, description regex, amount range)
- `action`: JSON of updates (e.g., `category_id`, `merchant`)
- `is_active`: Boolean flag to disable without deleting
- `created_at`, `updated_at`: Audit timestamps

## Relationships

- Linked to `User`
- Applied to `Transaction` objects during ingest

## Behaviors

- Rules are user scoped; no cross-user sharing
- Manual edits may create new rules when confirmed

## Related Logic

- [`transaction_rules_logic.py`](../../backend/app/sql/transaction_rules_logic.md)

## Related Docs

- [`docs/backend/features/transaction_rules.md`](../../../features/transaction_rules.md)
```
