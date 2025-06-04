## 📘 `7343a4630d46_adding_sync_cursor_webhook_log_for_plaid.py`
```markdown
# Migration: Add Plaid Sync Cursor

Alembic migration script that adds `sync_cursor`, `is_active`, and `last_error`
columns to the `plaid_accounts` table. Also creates a table for webhook logs.
Used during the transition to cursor-based transaction sync.
```
