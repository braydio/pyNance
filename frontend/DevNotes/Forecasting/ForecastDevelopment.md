#  Forecast Engine Integration Plan

---

##  Data Sources Overview

### 1.  Transactions Table (Plaid-based)

**Source:** `SELECT * FROM transactions;`

**Sample Fields:**

- `amount`: numeric (positive = income, negative = expense)
- `date`: ISO date string
- `account_id`: internal account reference
- `description`: label for transaction

**Usage:**

- Analyze recurring charges for forecast generation
- Summed to create "realized flows"

### 2.  Account History Data

**Source:** `SELECT * FROM account_history;`

**Fields:**

- `account_id`
- `balance`
- `date`

**Usage:**

- Primary driver for “Actuals” line in forecast chart
- Represents realized net worth over time

---

##  Forecast Engine Input Format

```ts
// Engine Inputs
type TransactionEntry = {
  date: string // YYYY-MM-DD
  amount: number
  description: string
}

type BalanceSnapshot = {
  date: string
  balance: number
}
```

**Adaptation Plan:**

- Accept above inputs
- Forecast based on recurring/manual entries
- Actuals via account balances or derived net flow
- Breakdown panel sourced from transactions

---

##  Usage Breakdown Table

| Feature               | Uses Transactions? | Uses Balance History? | Notes                                                     |
| --------------------- | ------------------ | --------------------- | --------------------------------------------------------- |
| Forecast line         | ✅ (optional)      | ❌                    | Derived from pattern detection or manual inputs           |
| Actuals line          | ✅ (aggregated)    | ✅                    | Primary from balance; fallback to transaction aggregation |
| Breakdown panel       | ✅                 | ❌                    | Top patterns/categories shown                             |
| Summary balance panel | ❌                 | ✅                    | Pull latest snapshot value                                |

---

##  Logic Integration Details

### 🔍 Recurring Pattern Detection (optional)

Use transaction text/date to infer repeated activity:

```ts
findRecurring(transactions) → [{ label: 'Auto Payment', amount: -200, frequency: 'monthly' }]
```

### 🧠 Combine Actuals Line from Both Sources

- **Primary:** Use `account_history` for accuracy
- **Fallback/Blend:** Sum `transactions` grouped by `date`

```ts
actualsLine = aggregate(account_history) ?? sum(transactions by date)
```

- Prefer both when aligned; log any variance

---

##  Chart Rendering Strategy

- Forecast: full future span
- Actuals: stop at today (marked clearly)
- Visual: optional fade or dash forecast line
- Toggle support: Monthly / Yearly views

---

##  Implementation Tasks

1. Integrate CSV transaction parser
2. Add mock data for balances + transactions
3. Align forecast and actuals in chart renderer
4. Generate panel summaries from transaction records

---

````markdown
# 📈 Forecast Engine Integration Plan

## ✅ Data Sources

### Transactions DB (Plaid-synced)

- Fields: `amount`, `date`, `description`, `account_id`
- Used for:
  - Actuals (aggregated by date)
  - Forecast patterns (optional)
  - Breakdown listing

### Account History (DB)

- Fields: `account_id`, `balance`, `date`
- Used for:
  - Actuals line (primary)
  - Summary panel current balance

## 🧠 Forecast Engine Inputs

```ts
type TransactionEntry = {
  date: string
  amount: number
  description: string
}

type BalanceSnapshot = {
  date: string
  balance: number
}
```
````

## 🛠️ Engine Adaptation

- Accept above types
- Plot forecast using manual + recurring inputs
- Plot actuals from balances or net daily activity
- Show actuals line stopping at current day
- Breakdown and panel use filtered + formatted transaction records

## 📊 Chart Plan

- Forecast line: full range
- Actuals line: stops at today
- Toggle: Month / Year
- Optional: recurring pattern detection from CSV

## 🔧 Next Steps

- Integrate real transaction data parser
- Inject mocked balance and transaction sets
- Render chart and panels with aligned values

```

```
