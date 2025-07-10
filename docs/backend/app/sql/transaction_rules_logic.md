# backend/app/sql Documentation

---

## \U0001F4D6 `transaction_rules_logic.py`

```markdown
# Transaction Rules SQL Logic

## Purpose

Provides helper functions to store and apply `TransactionRule` entries. Handles pattern matching and updates during transaction ingestion.

## Key Responsibilities

- Persist rule definitions in the database
- Query rules for a user during sync operations
- Apply matched actions to transaction rows

## Primary Functions

- `create_rule(user_id, match_criteria, action)`
  - Inserts a row into `transaction_rule` table
- `get_applicable_rules(user_id)`
  - Returns all active rules for the user
- `apply_rules(user_id, transaction)`
  - Mutates a transaction dict based on any matching rule

## Inputs

- `Transaction` metadata (merchant name, description, amount)
- User-scope rule set

## Outputs

- Updated transaction structures
- Logs of which rule was applied

## Internal Dependencies

- `models.TransactionRule`
- `db_session`

## Known Behaviors

- Rules are evaluated in insertion order
- Disabled rules are ignored
- Supports partial criteria (only merchant match, for example)

## Related Docs

- [`docs/backend/features/transaction_rules.md`](../features/transaction_rules.md)
```
