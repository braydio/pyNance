# 📊 Forecast Engine Module 1: Architecture & Data Design

## 🧠 Overview

This module defines the **forecasting engine's structure**, **data sources**, and **design rationale**. It establishes the logic used to calculate both forecasted and actual financial trajectories, including recurring income/expense simulation, actuals alignment, and input structures.

---

## 📚 Data Sources

### 1. Transactions (Plaid-based)

- Fields: `amount`, `date`, `account_id`, `description`
- Used for:

  - Deriving recurring patterns (optional)
  - Fallback calculation of actuals
  - Breakdown visualization

### 2. Account History

- Fields: `account_id`, `balance`, `date`
- Primary source for actuals line on forecast chart
- Reflects realized net worth snapshots over time

---

## 🧩 Input Structures

```ts
// Forecast Engine Input Types
interface TransactionEntry {
  date: string // YYYY-MM-DD
  amount: number
  description: string
}

interface BalanceSnapshot {
  date: string
  balance: number
}
```

- Actuals derived from `BalanceSnapshot[]`
- Forecasts use `TransactionEntry[]` or manual/recurring inputs

---

## 🔢 Feature Usage Breakdown

| Feature               | Uses Transactions? | Uses Balance History? | Notes                                            |
| --------------------- | ------------------ | --------------------- | ------------------------------------------------ |
| Forecast Line         | ✅ (optional)      | ❌                    | Derived from manual or recurring entries         |
| Actuals Line          | ✅ (fallback)      | ✅                    | Uses balances if available, transactions if not  |
| Breakdown Panel       | ✅                 | ❌                    | Category/pattern summaries from transactions     |
| Summary Balance Panel | ❌                 | ✅                    | Current balance pulled from most recent snapshot |

---

## 🔍 Forecast Engine Logic Flow

1. **Ingest Recurring Events**:

   - From `recurring_transactions`, `manual inputs`, or `findRecurring()`

2. **Generate Forecast Line**:

   - Project events forward using frequency and amount
   - Apply modifiers like `manualIncome`, `liabilityRate`
   - Output: `{ date, forecastValue }[]`

3. **Generate Actuals Line**:

   - Primary: From `account_history`
   - Fallback: `sum(transactions by date)`
   - Align to forecast timeline

4. **Compute Net Delta**:

   - `delta = forecast - actuals` (per date)

5. **Return Chart Data**:

   - X-axis labels (dates)
   - Y-axis: forecast\[], actuals\[], delta\[]

---

## 📈 Chart Rendering Plan

- Forecast: Full timeline
- Actuals: Only up to current day
- Visual features:

  - Toggle (Month/Year)
  - Tooltip on hover
  - Dynamic breakdowns by view type
  - Separate color styles for future vs past

---

## 🛠️ Next Actions (Module 1)

- [ ] Finalize input data normalization logic (transactions + balances)
- [ ] Ensure fallback to transaction sums if balance snapshots unavailable
- [ ] Mock actual `ForecastPoint[]` shape
- [ ] Prepare breakdown data structure for panel UI

---

_This is Module 1 of 2. Module 2 will focus on API routes, caching strategies, and backend integration logic._
