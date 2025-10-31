# `balance_history.py`

## Responsibility

- Persist normalized account balance snapshots derived from transactional deltas.
- Provide retrieval utilities that surface cached history for dashboards and API consumers.

## Key Functions

- [`calculate_daily_balances(account_id, current_balance, start_date, end_date)`](../../../../backend/app/services/balance_history.py): Queries `Transaction` rows, aggregates daily sums, and walks backwards from the normalized balance to emit dated balances.
- [`store_balance_history(account_id, balance_records)`](../../../../backend/app/services/balance_history.py): Upserts [`AccountHistory`](../../../../backend/app/models.py) rows per day, keeping existing entries synchronized.
- [`update_account_balance_history(account_id, days, force_update)`](../../../../backend/app/services/balance_history.py): Main entry point that normalizes the active balance via [`normalize_account_balance`](../../../../backend/app/utils/finance_utils.py) and coordinates calculation plus persistence.
- [`get_balance_history_from_db(account_id, days)`](../../../../backend/app/services/balance_history.py): Returns serialized history bounded by the requested time window.

## Dependencies & Collaborators

- SQLAlchemy models: `Account`, `AccountHistory`, `Transaction`.
- Shared helpers: [`app.utils.finance_utils.normalize_account_balance`](../../../../backend/app/utils/finance_utils.py).
- Complements [`account_history`](./account_history.md) for pure in-memory reconstruction and [`enhanced_account_history`](./enhanced_account_history.md) for cache-aware flows.

## Usage Notes

- Internal queries filter out transactions flagged as internal transfers through the `Transaction.is_internal` column, ensuring true cash movement.
- Consumers should invoke `update_account_balance_history` before reading when they need fresh coverage.
- Background jobs in
  [`tasks/balance_history_tasks.py`](../../../../backend/app/tasks/balance_history_tasks.py)
  orchestrate the periodic calls to `update_account_balance_history` and the
  bulk `update_all_accounts_balance_history` helper.
