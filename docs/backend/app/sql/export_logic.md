# backend/app/sql Documentation

---

## 📘 `export_logic.py`

```markdown
# Export Logic Module

## Purpose

Provides SQL-driven utilities and routines for exporting user data in structured formats. Enables CSV/JSON report generation, data archival, and export to third-party formats for integrations.

## Key Responsibilities

- Assemble and flatten transaction and budget data
- Enforce user-specific scope filtering
- Transform data into export-friendly schemas

## Primary Functions

- `export_transactions(user_id, filters)`

  - Returns raw rows with flattened transaction fields

- `export_balances(user_id, start_date, end_date)`

  - Generates a time-series dataset of balance trends

- `get_export_schema()`
  - Returns field mapping for headers and downstream processing

## Inputs

- Export scope: date range, accounts, tags, categories
- Optional normalization flags (currency formatting, anonymize data)

## Outputs

- Row-wise exportable data structures (list of dicts or SQL rows)
- Header mappings and export metadata

## Internal Dependencies

- `models.Transaction`, `models.Account`, `models.Category`
- SQLAlchemy session and joins

## Known Behaviors

- Flattens nested fields (e.g. category object → name)
- Sanitizes and formats date and currency fields
- Supports language localization for header labels

## Related Docs

- [`docs/export/export_formats.md`](../../export/export_formats.md)
- [`docs/frontend/tools/ExportInterface.md`](../../frontend/tools/ExportInterface.md)
```

---

Ready for `forecast_logic.py`?
