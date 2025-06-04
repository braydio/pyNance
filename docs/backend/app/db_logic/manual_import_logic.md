# backend/app/db_logic Documentation

---

## 📘 `manual_import_logic.py`

```markdown
# Manual Import Logic Module

## Purpose

Provides SQL utilities for handling manually uploaded or user-imported financial data. Converts CSV and user-entry transactions into persistent internal records, validating structure and resolving conflicts with synced data.

## Key Responsibilities

- Parse and validate incoming manual transaction rows
- Detect and prevent duplicates during import
- Normalize raw input formats into internal schema

## Primary Functions

- `parse_manual_csv(file_stream, user_id)`

  - Converts uploaded CSV into validated rows

- `deduplicate_manual_entries(user_id, parsed_rows)`

  - Filters out transactions already in the database (by signature)

- `import_manual_transactions(user_id, transactions)`
  - Commits parsed rows to the `Transaction` table

## Inputs

- CSV file or equivalent row data structure
- `user_id`, optional override flags
- Date, description, amount, account, memo

## Outputs

- Inserted `Transaction` records
- Summary of results: total parsed, imported, skipped, errored

## Internal Dependencies

- `models.Transaction`, `models.Account`
- Field mappers, schema validators, row normalizer
- File parser utility (`csv`, `pandas`)

## Known Behaviors

- Whitespace stripping and date coercion are always applied
- Skips lines with invalid date or amount formats
- Categorization is attempted at time of insert

## Related Docs

- [`docs/import/manual_import_guide.md`](../../import/manual_import_guide.md)
- [`docs/frontend/tools/ImportTool.md`](../../frontend/tools/ImportTool.md)
```

---

Ready for `recurring_logic.py`?
