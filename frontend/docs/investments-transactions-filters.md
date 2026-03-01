# Investments Transaction Filters

`frontend/src/views/Investments.vue` includes transaction-level filters for the Investments page transaction table.

## Supported filters

These controls are mapped directly to backend query parameter names through `fetchInvestmentTransactions(page, pageSize, filters)`:

- `account_id`
- `security_id`
- `type`
- `subtype`
- `start_date`
- `end_date`

## Persistence and pagination

- Filter selections are persisted in `localStorage` under `investments.transactionFilters`.
- Stored values are restored during view mount before the first transaction fetch.
- Any filter change triggers a fetch and resets transaction pagination to page 1.
