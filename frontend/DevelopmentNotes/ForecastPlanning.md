## Data Sources Overview

1. Transaction Data (Plaid-based)

CSV Sample Fields:

- amount: numeric value (positive = income, negative = expense)
- date: ISO date string
- account_id: maps to internal account
- description: transaction label

This is the most granular actual activity. These should:

- Inform future forecast patterns (e.g., recurring charges)
- Be summed to represent "realized flows"

2. Account History Data

These contain:
_account_id
_ balance
\_ date

These represent snapshots of total balance, useful to:

- Drive the “Actuals” line on the forecast chart
- Represent realized net worth

| Feature                   | Uses Transaction CSV?  | Uses Balance History? | Notes                                                              |
| ------------------------- | ---------------------- | --------------------- | ------------------------------------------------------------------ |
| Forecast line             | ✅ optionally          | ❌                    | Forecast derived from recurring pattern detection or manual inputs |
| Actuals line              | ✅ (aggregated by day) | ✅                    | Use balances if available; fallback to net daily transactions      |
| Breakdown panel           | ✅                     | ❌                    | Show top recurring patterns or categories from CSV                 |
| Summary balance estimates | ❌                     | ✅                    | Current balance from latest historical snapshot                    |

## Logic Flows

```

// Updated input types
type TransactionEntry = {
  date: string      // YYYY-MM-DD
  amount: number
  description: string
}

type BalanceSnapshot = {
  date: string
  balance: number
}

```

Recurring Transactions Detection

```
// psuedo:
findRecurring(transactions) → [{label: 'Auto Payment', amount: -200, frequency: 'monthly'}]

```

These will be fed into the forecast engine.

Combine Actuals from Both Sources

    Primary method: Use account_history snapshots for line chart actuals

    Fallback or enrichment: Calculate net flow from transactions per day:

```
actualsLine = aggregate(account_history)
           ?? sum(transactions grouped by date)

Use both if aligned (and log diff).
```

## Forecast Component (Planned Feature)

A new `Forecast.vue` component will be added under `/frontend/src/views/`. This component simulates a _dynamic financial forecast_, specifically focusing on the **net dollar delta** over a short-term period (e.g. 30 days).

### Phase 1: Frontend-Only Mock

- **Initial implementation will not depend on backend APIs.**
- Use mock data to simulate:

  - Recurring income and expenses.
  - Trends derived from transactions.
  - Investment growth or decline.
  - Liability deductions based on local rate inputs.

#### Key Features

- Real-time recalculation of forecast as inputs change.
- Accepts manual recurring income as a user parameter.
- Supports live user editing of:

  - Liability rates (manual or programmatic input).
  - Custom recurring transactions.

- Calculates net forecast as:
  `forecast = currentBalance + (inflows - outflows ± investmentReturn - liabilityImpact)`
- UI shows both:

  - A breakdown of forecast drivers.
  - A summary of projected balance and delta.

#### Future Integration Plans

- Bind forecast model to actual backend-calculated values.
- Pull recurring transactions and investment holdings from database/API.
- Integrate real account balance and transaction data.
- Visualize forecast over time (e.g., charting net change per day).

---
