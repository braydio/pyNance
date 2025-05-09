#  Forecast Engine Integration Plan

# Index

- [1] Data Sources Overview
- [2] Engine Input Formats
- [3] Breakdown Plan
- [4] Logic Integration Details
- [5] Chart Rendering Strategy
- [6] Implementation Steps 

##  Data Sources Overview

### 1. Transactions (plaid)

- Source: `transactions` table
- Fields in use: `amount`, `date`, `description`, `account_id`
- Used for:
  - Plotting actuals logic
  - Forecast generation trends (approx).

### 2. Account History

- Source: `account_history` table
- Fields: `backtraced`, `date`, `balance`
- Used for: realized net worth line


##  Engine Input Format

```ts
// Engine Entries
interface TransactionEntry {
  date: string
  amount: number
  description: string
}

// account history points
type BalanceSnapshot = {
  date: string
  balance: number
}
```

##  Breakdown Plan

- Forecast line is aggregated from recurring transactions + manual adjustments
[ Source: recurring_transactions ]
- Actuals line comes from account balances or estimated transactions
- Breakdown renders aggregated via description + money groups
