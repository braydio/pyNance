# 📊 Roadmap: Implement Account Balances Breakdown in `Accounts.vue`

## 1. Current Status

- Balance history endpoint exists: `GET /api/accounts/<account_id>/history` returns reverse-mapped daily balances (range param supported).
- Net change endpoint exists: `GET /api/accounts/<account_id>/net_changes`.
- Frontend uses these in Accounts summary and Transactions views; Cypress specs are scaffolded.

## 2. Backend

### 2.1 History Endpoint

Already implemented as `GET /api/accounts/<account_id>/history`.

### 2.2 Balance Calculation

Implemented via `services.account_history.compute_balance_history` using reverse deltas based on daily sums.

### 2.3 Testing

- Unit tests ensure reverse mapping produces correct balances.
- Endpoint returns continuous data without gaps.

## 3. Frontend

### 3.1 API Layer

Add to `frontend/src/api/accounts.js`:

```js
export async function fetchAccountHistory(accountId, startDate, endDate) {
  let url = `/api/accounts/${accountId}/history`;
  if (startDate && endDate) {
    url += `?start_date=${startDate}&end_date=${endDate}`;
  }
  const res = await fetch(url);
  return res.json();
}
```

### 3.2 Accounts.vue Integration

Use the existing `fetchAccountHistory` API and render a line chart (see `AccountsSummary` specs for examples).

### 3.3 Chart Component

- Create `frontend/src/components/charts/AccountBalanceHistoryChart.vue` based on `DailyNetChart`.
- Render a line chart of `date` vs `balance`.

### 3.4 Filter Controls

- Add dropdown with 7d, 30d, 90d, 365d ranges.
- Pass selected range to `fetchAccountHistory`.

### 3.5 Cypress Tests

- Visit `/accounts/:id`.
- Assert `[data-testid="history-chart"]` exists and tooltip shows
  "Balance: $X".
- Change `[data-testid="filter-dropdown"]` to a new range and verify
  new data loads.

## 4. Documentation

- Describe reverse-mapping algorithm and `/accounts/:id/history` endpoint.
- Document usage of `AccountBalanceHistoryChart` in frontend guide.

## 5. Deliverables

- History endpoint with reverse-mapped balances.
- Frontend API function and Accounts.vue integration.
- `AccountBalanceHistoryChart` component with range filters.
- Backend unit tests and Cypress tests.
- Updated developer documentation.

## 6. Next Steps (Prioritized)

1. Add backend unit tests for history computation and endpoint ranges.
2. Frontend: polish range controls (7d/30d/90d/365d) and empty states.
3. Expose account-level annotations (e.g., large internal transfers) overlaid on history.
