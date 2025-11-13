# 📘 `c6e1f4b0d2a3_create_transaction_rules_table.py`

```markdown
# Migration: Create Transaction Rules Table

Introduces the `transaction_rules` table backing the automated
categorization engine.
```

## Summary

- Creates the `transaction_rules` table with JSON `match_criteria` and
  `action` fields plus an `is_active` flag.
- Adds an index on `user_id` so lookups during sync remain fast.
- Establishes a FK to `users` (if present in the baseline) to scope rules per user.

## Why this matters

The rules engine is evaluated during transaction ingest and when users apply
manual rules from the UI. Missing this table will surface 500s from endpoints
like `/api/transactions/rules` and block automatic categorization.

## Upgrade Steps

```bash
flask --app backend.run db upgrade
```

Once applied, verify the table exists and indexes are healthy:

```sql
-- psql
\d+ transaction_rules;
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'transaction_rules';
```

## Verification Checklist

- API `GET /api/transactions/rules` returns an empty list (200) instead of 500.
- Creating a rule via the UI or `POST /api/rules/` inserts a row.
- Applying rules during a rescan updates matching transactions without errors.

## Rollback Considerations

Dropping this revision removes the `transaction_rules` table and its index,
disabling rule-based categorization. If you must downgrade:

1. Export existing rules for safety: `COPY transaction_rules TO STDOUT WITH CSV`.
2. Downgrade Alembic: `flask --app backend.run db downgrade -1`.
3. Re-run an ingest or categorization pass to confirm the app behaves as expected.

## Related Code Paths

- `backend/app/routes/transactions.py` rules endpoints
- `backend/app/services/` categorization/rules logic
- `backend/app/models/transaction_models.py` rule model definitions
