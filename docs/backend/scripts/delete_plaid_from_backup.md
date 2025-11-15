## 📘 `delete_plaid_from_backup.py`

````markdown
# Delete Plaid Accounts from Backup Snapshot

Utility script for cleaning up Plaid-linked accounts based on a legacy SQLite
dashboard backup. The tool is useful when decommissioning old Items or
reconciling a fresh PostgreSQL database with the Plaid environment.

**Location:** `backend/scripts/delete_plaid_from_backup.py`

## How It Works

1. Opens the legacy SQLite DB at `app/data/backup_dashboard_database.db` (or a
   custom path).
2. Selects all rows from `accounts` where `link_type = 'plaid'`.
3. For each account, optionally calls the backend endpoint:

   ```http
   DELETE /api/plaid/transactions/delete_account
   ```
````

which revokes the Plaid item and deletes the linked account and related
records in PostgreSQL.

By default the script runs in **dry-run** mode and only prints which accounts
would be deleted.

## Usage

From the `backend/` directory:

```bash
python scripts/delete_plaid_from_backup.py
```

To execute deletions against a running backend:

```bash
python scripts/delete_plaid_from_backup.py --execute --base-url http://localhost:5000
```

Use caution: with `--execute` this will permanently delete accounts and their
associated data via the API.

```

```
