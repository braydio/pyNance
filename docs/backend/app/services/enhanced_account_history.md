# `enhanced_account_history.py`

## Responsibility
- Serve as a cache-aware facade for account balance history that first checks persisted snapshots before recomputing from transactions.
- Keep the `AccountHistory` table synchronized across multiple lookback windows (7, 30, 90, 365 days).

## Key Functions
- [`get_or_compute_account_history(account_id, days, force_recompute)`](../../../../backend/app/services/enhanced_account_history.py): Retrieves cached history within the requested window or triggers a recomputation when entries are stale or incomplete.
- [`compute_fresh_history(account_id, current_balance, start_date, end_date)`](../../../../backend/app/services/enhanced_account_history.py): Aggregates `Transaction` activity and delegates balance reconstruction to [`compute_balance_history`](./account_history.md).
- [`cache_history(account_id, user_id, history)`](../../../../backend/app/services/enhanced_account_history.py): Replaces persisted history rows with freshly generated data, rounding via `Decimal("0.01")` precision.
- [`update_account_balance_history(account_id, force_update)`](../../../../backend/app/services/enhanced_account_history.py): Convenience wrapper that refreshes the cache across standard timeframes.

## Dependencies & Collaborators
- SQLAlchemy models: `Account`, `AccountHistory`, `Transaction`.
- Relies on [`app.utils.finance_utils.normalize_account_balance`](../../../../backend/app/utils/finance_utils.py) to translate stored balances into comparable values.
- Shares lower-level reconstruction logic with [`account_history`](./account_history.md) and complements the persistence flows in [`balance_history`](./balance_history.md).

## Usage Notes
- Cached histories are considered stale when their most recent `updated_at` timestamp is older than 24 hours.
- `Transaction.is_internal` rows are filtered out to avoid double-counting transfers when recomputing histories.
