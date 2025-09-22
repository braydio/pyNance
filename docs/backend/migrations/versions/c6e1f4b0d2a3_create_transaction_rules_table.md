# 📘 `c6e1f4b0d2a3_create_transaction_rules_table.py`

```markdown
# Migration: Create Transaction Rules Table

Introduces the `transaction_rules` table backing the automated
categorisation engine.
```

## Summary

- Creates the `transaction_rules` table with JSON `match_criteria` and
  `action` fields plus an `is_active` flag.
- Adds an index on `user_id` so lookups during sync remain fast.

## Upgrade Steps

```bash
flask --app backend.run db upgrade
```

This ensures the table is present before enabling the transaction rules
API.

## Downgrade Impact

Dropping this revision removes the `transaction_rules` table and its
index, disabling rule-based categorisation.
