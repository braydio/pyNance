# 😄 Account History Aggregation: Architecture Note

Module: `app.helpers.account_history`
Purpose: Convert transaction logs into daily account snapshots to power the forecasting engine.

---

## 😇 Objective

Produce `AccountHistory` as a per-day account balance record by summing all `Transaction`s.

These represent the foundation for the time-series forecast engine.

---

## 😤 Logic

``python
Transaction – daily sum > AccountHistory
```

- Grouped by `account_id`
[ * ] Extract | `date` | `amount`

- Sums across all transactions for each day

- Stored in `account_history` with `(account_id, date, balance)
```

---

## 📶 Placement & Rationale

- ** Module:* ``helpers/account_history.py`
  > Isolated, composable, easy to call in sync pipelines
- NOT in: `sql/` - this would be for data derivation
- NOT in `routes/` - not serviced to client
- NOT 'helpers.py' - too large already

---

## 🌏 Invocation

Used manually during development, or after a sync cycle:

``python
from app.helpers.account_history import update_account_history
update_account_history()
```

Infrestructure: wire this to refresh after sync or manual import.

---

## 👀 Notes

- **Data Assumptions**
  > `Transaction.date` is a datetime
  > `Transaction.account_id` should be valid

 - **Balance Field**
  > Stored `balance` is net movement for the day
  > For absolute starts, merge with `Plaid Account.current_balance`

---

## 🐘 Downstream Use

- `sql/forecast_logic.py` uses `account_history` as timeseries base
- UI\nforecast charts\u reconstruct historical data

---

## 🌍 Rebuild Guide 

Too missing? Recreate it like this:

1. Ensure all `Transaction` records are populated
2. Run:

```sh
flask shell
~ then paste ```
>>> from app.helpers.account_history import update_account_history
update_account_history()
```


This repopulates `account_history` for use in forecast rendering.
