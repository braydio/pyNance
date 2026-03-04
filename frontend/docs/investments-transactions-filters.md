# Investments Transaction Filters

`frontend/src/views/Investments.vue` includes transaction-level filters for the Investments page transaction table.

## Supported filters

These controls are mapped directly to backend query parameter names through `fetchInvestmentTransactions(page, pageSize, filters)`. The `user_id` is also passed inside `filters` so the request uses backend query parameter names exactly:

- `account_id`
- `security_id`
- `type`
- `subtype`
- `start_date`
- `end_date`

The API helper only forwards the supported keys above (plus paging) so no unrelated client-side keys are sent to the backend.

## Persistence and pagination

- Filter selections are persisted in `localStorage` under `investments.transactionFilters`.
- Stored values are restored during view mount before the first transaction fetch.
- Any filter change triggers a fetch and resets transaction pagination to page 1.
