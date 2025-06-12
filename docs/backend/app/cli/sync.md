## 📘 `sync.py`
```markdown
# CLI Sync Command

Defines the `sync-accounts` Click command for manual refreshes. The command now
creates the Flask application and context itself before invoking
`refresh_all_accounts()`. This delegates actual syncing to
`sync_service.sync_account()` for each stored account.

**Dependencies**: `click`, `app.create_app`,
`account_refresh_dispatcher.refresh_all_accounts`.
```
