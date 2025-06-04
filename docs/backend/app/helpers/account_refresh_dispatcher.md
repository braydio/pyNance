## 📘 `account_refresh_dispatcher.py`
```markdown
# Account Refresh Dispatcher

Provides `refresh_all_accounts()` which iterates through stored accounts and
triggers synchronization for each via either `teller_helpers` or
`plaid_helpers`. Runs within an application context and logs progress.

**Dependencies**: `app`, `app.models.Account`, `app.helpers.teller_helpers`,
`app.helpers.plaid_helpers`, `app.config.logger`.
```
