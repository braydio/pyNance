## 📘 `sync.py`
```markdown
# CLI Sync Command

Defines the `sync-accounts` Click command used for manual account refreshes.
When executed, it calls `refresh_all_accounts()` from
`app.helpers.account_refresh_dispatcher` within the Flask application context.
Useful for scheduled jobs or development.

**Dependencies**: `click`, `flask.cli`, `refresh_dispatcher.refresh_all_accounts`.
```
