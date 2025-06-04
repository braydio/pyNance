## 🔧 Forecast Sync Logic & Architecture Refactor – Process Note

### 📁 Summary of Reviewed Modules

#### 1. `/db_logic/` Directory

* `account_logic.py`: Large file handling balances, aggregates, linking accounts
* `forecast_logic.py`: ✅ Contains newly added `get_latest_balance_for_account`, `update_account_history`, `generate_forecast_line`, `calculate_deltas`
* `recurring_logic.py`: Logic for detecting and managing recurring transactions
* `manual_import_logic.py`, `export_logic.py`, `category_logic.py`: No forecast overlap

#### 2. `/helpers/` Directory

* `plaid_helpers.py`: Pulls accounts, transactions from Plaid; does not persist balances
* `teller_helpers.py`: Fetches Teller account objects, returns JSON only; does not persist balances
* `account_refresh_dispatcher.py`: Handles periodic sync, routes to provider-specific logic
* `refresh_dispatcher.py`: Redundant, likely legacy
* `helpers.py`, `import_helpers.py`: Misc utilities, not relevant to forecast

### ⚠️ Issues & Observations

1. **Balance Sync Not Persistent**
   Neither `plaid_helpers` nor `teller_helpers` write balances into `AccountHistory`. This causes `forecast.py` to work off stale or incomplete data.

2. **Duplication Risk in `account_logic.py`**
   Some balance/transaction utilities in `account_logic.py` overlap with functions now centralized in `forecast_logic.py`. These should be consolidated.

3. **Dispatcher Lacks `user_id` Threading**
   `account_refresh_dispatcher.py` calls `get_teller_accounts()` without passing `user_id`, which prevents `update_account_history()` from executing correctly.

4. **Redundant Dispatcher**
   `refresh_dispatcher.py` appears to duplicate `account_refresh_dispatcher.py`. It should be deprecated.

### ✅ Refactor Plan

#### ✅ `forecast_logic.py`

* Keep all forecast-related logic here:

  * `get_latest_balance_for_account`
  * `update_account_history`
  * `generate_forecast_line`
  * `calculate_deltas`

#### 🔁 `plaid_helpers.py` and `teller_helpers.py`

* Inject `update_account_history()` calls after balance fetch
* Update method signatures to accept `user_id`
* Example (Teller):

```python
accounts = response.json()
for acct in accounts:
    update_account_history(account_id=acct["id"], user_id=user_id, balance=acct["available_balance"])
```

#### 🔁 `account_refresh_dispatcher.py`

* Pass `user_id` to sync helpers:

```python
sync_teller_account(account, user_id=account.user_id)
```

* Modify sync functions to accept and forward `user_id`

#### ❌ Remove `refresh_dispatcher.py`

* Archive this file unless it contains logic not present in `account_refresh_dispatcher.py`

#### 🧪 Testing Required

* Forecast endpoint returns daily labels and realistic forecast/actual/delta arrays
* AccountHistory contains 3+ entries per week (Teller) or per provider policy
* Dispatcher runs on cron and syncs data without manual intervention

---
