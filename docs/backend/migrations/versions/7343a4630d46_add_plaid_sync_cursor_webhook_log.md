# 📘 `7343a4630d46_add_plaid_sync_cursor_webhook_log.py`

```markdown
# Migration: Add Plaid Sync Cursor & Webhook Log Table

Tracks Plaid's delta-based transaction sync by adding cursor metadata to
`plaid_accounts` and introduces a dedicated `plaid_webhook_logs` audit table.
```

## Summary

- Adds `sync_cursor`, `is_active`, and `last_error` columns to
  `plaid_accounts` with a default of `true` for `is_active`.
- Creates the `plaid_webhook_logs` table used by
  `app.routes.plaid_webhook` to persist incoming webhook payloads.

## Upgrade Steps

1. Run the Alembic upgrade command:

   ```bash
   flask --app backend.run db upgrade
   ```

2. Existing Plaid accounts receive `is_active = true` and can now store
   sync cursors plus the last error message.
3. New webhook deliveries will be captured in `plaid_webhook_logs`.

## Downgrade Impact

- Dropping the migration removes the webhook log table and deletes the
  cursor-related columns from `plaid_accounts`, reverting the sync
  implementation to its pre-cursor state.
