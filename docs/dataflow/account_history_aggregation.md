# 😄 Account History Aggregation: Architecture Note

**Module:** `app.helpers.account_history`
**Purpose:** Convert transaction logs into daily account snapshots to power the forecasting engine.

---

## 😇 Objective

Produce `AccountHistory` as a per-day account balance record by summing all `Transaction`s.

These represent the foundation for the time-series forecast engine.

---

## 😤 Logic

```python
from sqlalchemy import func

from app.extensions import db
from app.models import Transaction, AccountHistory

def update_account_history():
    """
    Aggregate daily transaction totals into AccountHistory entries per account.
    This is used as the backend data source for forecasting.
    """
    print("🔁 Starting account history aggregation...")

    grouped = (
        db.session.query(
            Transaction.account_id,
            func.date(Transaction.date).label("tx_date"),
            func.sum(Transaction.amount).label("balance"),
        )
        .group_by(Transaction.account_id, func.date(Transaction.date))
        .all()
    )

    records = [
        AccountHistory(account_id=aid, date=tx_date, balance=bal)
        for aid, tx_date, bal in grouped
    ]

    db.session.bulk_save_objects(records)
    db.session.commit()

    print(f"✅ AccountHistory updated with {len(records)} records.")
```

- Grouped by `account_id`
- Extracts `date` and `amount`
- Sums across all transactions for each day
- Stored in `account_history` with `(account_id, date, balance)`

---

## 📆 Placement & Rationale

- **Module:** `helpers/account_history.py`

  > Isolated, composable, easy to call in sync pipelines

- **NOT** in `sql/` — that is for derived/transform logic
- **NOT** in `routes/` — not client-facing
- **NOT** in `helpers.py` — already too large

---

## 🌏 Invocation

Used manually during development, or after a sync cycle:

```python
from app.helpers.account_history import update_account_history
update_account_history()
```

Infrastructure: wire this to refresh after sync or manual import.

---

## 👀 Notes

- **Data Assumptions**:

  - `Transaction.date` is a datetime
  - `Transaction.account_id` is valid

- **Balance Field**:

  - Stored `balance` is net movement for the day
  - For absolute starts, merge with `PlaidAccount.current_balance`

---

## 🐘 Downstream Use

- `sql/forecast_logic.py` uses `account_history` as the time-series base
- UI forecast charts reconstruct historical data from it

---

## 🌍 Rebuild Guide

Too missing? Recreate it like this:

1. Ensure all `Transaction` records are populated
2. Run:

```sh
flask shell
```

Then paste:

```python
>>> from app.helpers.account_history import update_account_history
>>> update_account_history()
```

This repopulates `account_history` for use in forecast rendering.
