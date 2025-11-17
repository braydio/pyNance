## 📘 `import_accounts.py`

````markdown
# Import Accounts from CSV

Imports or updates rows in the `accounts` table from a dashboard CSV export.
This is intended for bootstrapping a new PostgreSQL database from a legacy
SQLite or CSV dump.

**Location:** `backend/app/cli/import_accounts.py`

## Expected Columns

The script accepts a CSV with at least:

- `account_id` (business key, required)
- `user_id`
- `name`
- `type`, `subtype`
- `institution_name`
- `status`
- `balance`
- `link_type` (`manual` or `plaid`)
- `is_hidden`
- `institution_db_id`

Extra columns are ignored.

## Usage

From the `backend/` directory:

```bash
flask import-accounts --csv-path app/data/Accounts.csv
```
````

Rows are upserted by `account_id`. Status values are normalized to the account
status enum and link types are coerced to `manual` or `plaid`.

```

```
