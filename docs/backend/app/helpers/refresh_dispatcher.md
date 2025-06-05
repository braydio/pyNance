## 📘 `refresh_dispatcher.py`
```markdown
# Deprecated Refresh Dispatcher

Legacy version of account refresh logic. It duplicates
`account_refresh_dispatcher.py` and has been fully replaced by the
`sync_service`. This file remains for historical reference only and can be
deleted once all callers have migrated.

**Dependencies**: `app.models.Account`, `teller_helpers`, `plaid_helpers`,
`app.config.logger`.
```
