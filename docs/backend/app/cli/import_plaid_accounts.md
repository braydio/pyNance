## 📘 `import_plaid_accounts.py`

````markdown
# Import PlaidAccount Rows from CSV

Imports or updates rows in the `plaid_accounts` table from a CSV export,
linking each to an existing `accounts.account_id`. This is useful when
re-hydrating Plaid metadata after a migration.

**Location:** `backend/app/cli/import_plaid_accounts.py`

## Expected Columns

The CSV should include:

- `account_id` (required; must exist in `accounts`)
- `access_token`
- `item_id`
- `institution_id`
- `webhook`
- `last_refreshed`
- `sync_cursor`
- `is_active`
- `last_error`
- `plaid_institution_id`
- `institution_db_id`
- `product`

## Usage

From the `backend/` directory:

```bash
flask import-plaid-accounts --csv-path app/data/PlaidAccounts.csv
```
````

Rows are upserted by `account_id`. Any row whose `account_id` does not exist
in `accounts` is skipped to preserve referential integrity.

```

```
