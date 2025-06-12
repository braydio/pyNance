## 📘 `account_refresh_dispatcher.py`
```markdown
# Account Refresh Dispatcher

Provides `refresh_all_accounts()` which iterates through stored accounts and
invokes `sync_service.sync_account()` for each. The dispatcher no longer
creates its own Flask application; callers must enter an app context first.

**Dependencies**: `app.models.Account`, `app.services.sync_service`,
`app.config.logger`.
```
