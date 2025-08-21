# 📊 Roadmap: Implement Account Balances Breakdown in `Accounts.vue`

## 1. Current Status
- `Accounts.vue` should display a historical balance chart, but existing charts are placeholders and the history API call is missing.
- Cypress scaffold exists at `frontend/src/views/__tests__/AccountsSummary.cy.js`.
- Backend already contains accounts and transactions models.

## 2. Backend
### 2.1 History Endpoint
Create `/api/accounts/:id/history` returning:

```
{
  "accountId": "uuid",
  "asOfDate": "YYYY-MM-DD",
  "balances": [
    {"date": "YYYY-MM-DD", "balance": 1523.21},
    {"date": "YYYY-MM-DD", "balance": 1499.10}
  ]
}
```

### 2.2 Balance Calculation
- Inputs: current account balance and all transactions.
- Process:
  1. Sort transactions by descending date.
  2. Start from today's balance.
  3. For each day, reverse that day's transactions to derive the previous balance.
  4. Record the resulting balance.
- Pseudocode:

```python
balances = {}
balance = account.current_balance
for day in dates_descending:
    for tx in transactions_on(day):
        balance += tx.amount if tx.type == "debit" else -tx.amount
    balances[day] = balance
```

- Example SQL aggregation:

```sql
SELECT date, SUM(amount) AS delta
FROM transactions
WHERE account_id = :id
GROUP BY date
ORDER BY date DESC;
```

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
```js
import { fetchAccountHistory } from "@/api/accounts";

const accountHistory = ref([]);

onMounted(async () => {
  const res = await fetchAccountHistory(route.params.id);
  if (res.status === "success") {
    accountHistory.value = res.history;
  }
});
```

Replace placeholder chart with:

```vue
<AccountBalanceHistoryChart :balances="accountHistory" />
```

### 3.3 Chart Component
- Create `frontend/src/components/charts/AccountBalanceHistoryChart.vue` based on `DailyNetChart`.
- Render a line chart of `date` vs `balance`.

### 3.4 Filter Controls
- Add dropdown with 7d, 30d, 90d, 365d ranges.
- Pass selected range to `fetchAccountHistory`.

### 3.5 Cypress Tests
- Visit `/accounts/:id`.
- Assert chart renders and tooltip shows "Balance: $X".
- Verify filter dropdown switches ranges.

## 4. Documentation
- Describe reverse-mapping algorithm and `/accounts/:id/history` endpoint.
- Document usage of `AccountBalanceHistoryChart` in frontend guide.

## 5. Deliverables
- History endpoint with reverse-mapped balances.
- Frontend API function and Accounts.vue integration.
- `AccountBalanceHistoryChart` component with range filters.
- Backend unit tests and Cypress tests.
- Updated developer documentation.

## 6. Next Steps
1. **Backend**
   - Refactor `app/sql/forecast_logic.py:update_account_history` to use reverse mapping.
   - Write migration to backfill `AccountHistory`.
2. **Frontend**
   - Implement `fetchAccountHistory`.
   - Build and integrate `AccountBalanceHistoryChart` and filter controls.
3. **Testing**
   - Add backend tests for history calculation.
   - Extend Cypress tests for chart and filters.
