# Accounts Experience Roadmap

## Snapshot

- `/api/accounts/<account_id>/history` and `/api/accounts/<account_id>/net_changes` already serve balance history and deltas for the UI.
- `app/services/account_history.compute_balance_history` reverse-maps transaction deltas into daily balances and is exercised by `tests/test_account_history_service.py`.
- The Accounts summary view consumes the history endpoint today, but the detail page still needs richer visualisation and filtering.

## Backend focus areas

1. **History fidelity**
   - Extend unit tests to cover explicit `start_date`/`end_date` windows and sparse transaction scenarios.
   - Add integration coverage in `tests/test_api_account_history.py` for typical and edge accounts (empty history, single-day balance, multi-currency guards).
2. **Telemetry**
   - Instrument history fetch counts, cache hits, and service timing so regressions are traceable.
   - Surface errors via structured logging; consider emitting Prometheus counters alongside existing logs.

## Frontend focus areas

1. **Dedicated history chart**
   - Build `frontend/src/components/charts/AccountBalanceHistoryChart.vue` patterned after `DailyNetChart` with explicit props for `points`, `currency`, and `emptyState` copy.
   - Fetch data via `frontend/src/api/accounts.js#fetchAccountHistory(accountId, startDate?, endDate?)` and normalise to chronological order before rendering.
2. **Range controls & insights**
   - Introduce presets (7d/30d/90d/365d/custom) with accessible toggle UI and persist the last selection per account.
   - Annotate notable balance swings (large transfers, predicted bills) once telemetry is available.

## Quality & coverage

- Expand Cypress component/e2e specs under `frontend/src/views/__tests__/AccountsSummary.cy.js` (or add a dedicated history spec) to exercise chart rendering, range toggles, and empty states.
- Keep backend contract tests fast—stub Plaid/Teller dependencies and reuse factories from `tests/fixtures/` where possible.
- Ensure newly exposed metrics are asserted in monitoring smoke tests or documented manual verification steps.

## Documentation updates

- Record the reverse-mapping algorithm and chart usage patterns in `docs/frontend/` once the UI ships.
- Update API reference entries for `/api/accounts/<id>/history` with query parameter examples and response schema notes.

## Next milestone (Q4 target)

1. Ship the chart component with responsive layout support.
2. Land backend telemetry and associated alerting runbooks.
3. Iterate on annotations/insights once the base visualisation is stable.

_Last updated: 2025-09-10_
