# `account_history.py`

## Responsibility

- Reverse-map historical daily balances for a single account based on a known ending balance and dated transaction deltas.
- Provide currency-safe rounding helpers that are reused by higher-level history services.

## Key Function

- [`compute_balance_history(starting_balance, transactions, start_date, end_date)`](../../../../backend/app/services/account_history.py): Builds a chronological series of `{date, balance}` rows by iterating from `end_date` backwards, aggregating transaction deltas per day, and emitting ISO-formatted dates.

## Dependencies & Collaborators

- Relies on Python `decimal.Decimal` arithmetic to maintain currency precision.
- Consumed directly by [`enhanced_account_history`](./enhanced_account_history.md) when composing cached histories.
- Paired with database persistence helpers in [`balance_history`](./balance_history.md).

## Usage Example

```python
from backend.app.services.account_history import compute_balance_history
from decimal import Decimal
from datetime import date

history = compute_balance_history(
    starting_balance=Decimal("1250.55"),
    transactions=[{"date": date(2024, 6, 1), "amount": Decimal("-45.12")}],
    start_date=date(2024, 6, 1),
    end_date=date(2024, 6, 7),
)
```
