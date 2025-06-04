## 📘 `account_history_helper.py`
```markdown
# Account History Aggregation

Contains `update_account_history()` which sums daily transaction totals for each
account and persists them in the `AccountHistory` table. This provides the data
needed for forecasting account balances.

**Dependencies**: `app.extensions.db`, `app.models.Transaction`, `app.models.AccountHistory`.
```
