# 📊 Roadmap: Implement Account Balances Breakdown in `Accounts.vue`

## 1. **Understand Current State**

- File of interest: `frontend/src/views/Accounts.vue` (\~7KB).
- Test coverage: `frontend/src/views/__tests__/AccountsSummary.cy.js`.
- Related backend endpoints: Likely in `backend` (transactions + accounts).
- Current issue: Charts meant to show historical balances are **broken** (likely API mismatch or data not computed).
- Goal: Show daily account balances by starting from today’s balance and working backward using transactions.

---

## 2. **Backend Work**

### 2.1 API Check

- Inspect `backend/` for:

  - `accounts` model
  - `transactions` model
  - Any existing endpoint like `/api/accounts/:id/transactions`

- If missing:

  - Create new endpoint `/api/accounts/:id/history` returning:

    ```json
    {
      "accountId": "uuid",
      "asOfDate": "2025-08-21",
      "balances": [
        { "date": "2025-08-20", "balance": 1523.21 },
        { "date": "2025-08-19", "balance": 1499.1 }
      ]
    }
    ```

### 2.2 Balance Calculation Algorithm

- Input:

  - Today’s balance (stored in account table).
  - Transaction list for that account.

- Process:

  - Sort transactions by descending date.
  - Start from today’s balance.
  - For each day:

    - Subtract/add transactions that happened that day.
    - Store resulting balance.

  - Continue until reaching oldest transaction.

- Pseudocode:

  ```python
  balances = {}
  balance = account.current_balance
  for day in reversed(dates):
      for tx in transactions_on(day):
          balance -= tx.amount if tx.type == 'debit' else -tx.amount
      balances[day] = balance
  ```

- Optimize with SQL:

  ```sql
  SELECT date, SUM(amount) AS delta
  FROM transactions
  WHERE account_id = :id
  GROUP BY date
  ORDER BY date DESC;
  ```

---

## 3. **Frontend Work**

### 3.1 Data Layer

- File: `frontend/src/api/accounts.js` (create if missing).
- Add method:

  ```js
  export async function getAccountHistory(accountId) {
    const res = await fetch(`/api/accounts/${accountId}/history`);
    return res.json();
  }
  ```

### 3.2 Update `Accounts.vue`

- Fetch history in `onMounted`.
- Store in `ref`:

  ```js
  const balances = ref([]);
  onMounted(async () => {
    balances.value = await getAccountHistory(route.params.id);
  });
  ```

### 3.3 Chart Component

- Use `recharts` or existing chart lib (look at `Dashboard.vue` which has working charts).

- Example:

  ```vue
  <LineChart :data="balances">
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip />
    <Line type="monotone" dataKey="balance" stroke="#8884d8" />
  </LineChart>
  ```

- Add **filter controls**:

  - Dropdown: "Last 7 days, 30 days, 90 days, 1 year".
  - Default: 30 days.

- Add **account switcher** if multiple accounts are loaded.

---

## 4. **Testing**

### 4.1 Cypress Tests (`frontend/src/views/__tests__/AccountsSummary.cy.js`)

- Add test:

  - Visit `/accounts/:id`
  - Check chart renders.
  - Validate axis labels (dates).
  - Validate line plot not empty.

### 4.2 Backend Tests (`tests/`)

- Unit test history calculation logic.
- Verify balance reconciliation matches database.

---

## 5. **Docs & Guides**

- Update `frontend/docs/` with:

  - Chart usage.
  - API structure (`/accounts/:id/history`).

- Update `CONTRIBUTING.md` for dev workflow.

---

## 6. **Deliverables**

- ✅ Backend endpoint: `/api/accounts/:id/history`
- ✅ Frontend API call: `getAccountHistory(accountId)`
- ✅ Balance calculation logic
- ✅ `Accounts.vue` chart integration
- ✅ Tests for backend + frontend
- ✅ Docs updated

---

## 7. **Next Steps**

1. Read `Accounts.vue` implementation for existing chart placeholders.
2. Inspect backend for `accounts` + `transactions` models.
3. Build backend endpoint.
4. Wire frontend + render chart.
5. Add tests.

---

# V2 -- EXPANDED ROADMAP

---

# 📊 Expanded Roadmap for `Accounts.vue` Balance Breakdown

## 1. **Current Implementation Issues**

- `Accounts.vue` imports **charts**:

  - `NetYearComparisonChart`
  - `AssetsBarTrended`
  - `AccountsReorderChart`

- None of these charts receive **account history data** — they’re placeholders.
- Data loaded:

  - `fetchNetChanges(accountId)` → populates `newSummary`.
  - `fetchRecentTransactions(accountId)` → populates `recentTransactions`.

- **Missing**: API call for **daily account balances**.

---

## 2. **Backend Fix**

### 2.1 Add Endpoint

File: `backend/api/accounts.py` (or equivalent)

```python
@router.get("/accounts/{account_id}/history")
def get_account_history(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")

    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .order_by(Transaction.date.desc())
        .all()
    )

    balances = []
    balance = account.current_balance
    current_date = datetime.today().date()

    # Walk backwards
    for day in range(0, 365):  # 1 year default
        d = current_date - timedelta(days=day)
        day_tx = [t for t in transactions if t.date.date() == d]
        for tx in day_tx:
            balance -= tx.amount if tx.type == "debit" else -tx.amount
        balances.append({"date": str(d), "balance": float(balance)})

    return {"accountId": account_id, "balances": list(reversed(balances))}
```

---

## 3. **Frontend Fix**

### 3.1 API Layer

File: `frontend/src/api/accounts.js`

```js
export async function fetchAccountHistory(accountId) {
  const res = await fetch(`/api/accounts/${accountId}/history`);
  return res.json();
}
```

### 3.2 `Accounts.vue` Changes

At top of `<script setup>`:

```js
import { fetchAccountHistory } from "@/api/accounts";

const accountHistory = ref([]);
```

In `onMounted`:

```js
const res = await fetchAccountHistory(accountId);
accountHistory.value = res.balances;
```

### 3.3 New Chart

Replace placeholder in template:

```vue
<section class="p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md">
  <h3 class="font-bold text-lg">Account Balance Over Time</h3>
  <LineChart
    :width="600"
    :height="300"
    :data="accountHistory"
  >
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip />
    <Line type="monotone" dataKey="balance" stroke="#82ca9d" />
  </LineChart>
</section>
```

---

## 4. **Testing**

### 4.1 Cypress (`AccountsSummary.cy.js`)

Add test:

```js
it("renders balance history chart", () => {
  cy.visit("/accounts/acc1");
  cy.get(".recharts-wrapper").should("exist");
  cy.contains("Account Balance Over Time");
});
```

### 4.2 Backend

- Unit test history endpoint.
- Validate balance sequence.

---

## 5. **Migration Path**

1. Add `/accounts/:id/history` backend route.
2. Add `fetchAccountHistory` API.
3. Modify `Accounts.vue`:

   - New `ref` (`accountHistory`).
   - Fetch in `onMounted`.
   - Render `LineChart`.

4. Write frontend & backend tests.
5. Clean up old placeholder charts if unused.

---

## 6. **Visual Output**

✅ Working line chart of daily balances
✅ Filter by 7/30/90/365 days (extend with dropdown)
✅ Data accurate via transaction reconciliation

---

Would you like me to **map the `frontend/src/components/charts/` directory** so I can see if `AccountsReorderChart` or `AssetsBarTrended` can be reused for this new balance chart, instead of writing a new chart component from scratch?
