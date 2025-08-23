# Mock Data Canvas: pyNance Views

This file outlines rendering requirements for each view in the `frontend/src/views` files and their supporting components.

----

## Accounts.vue

**Required Data**

``json
{
  userName: "Test User",
  selectedProducts: ["auth", "transactions"],
  accountGroups: ["Checking", "Savings", "Credit"],
  activeAccountGroup: "Checking",
  showTokenForm: false,
  accounts: [
    { id: 1, name: "Primary Checking", balance: 1234.56, institution: "Bank A", group: "Checking" },
    { id: 2, name: "Emergency Savings", balance: 5678.90, institution: "Bank B", group: "Savings" }
  ],
  assetsTrend: [
    { date: "2025-01", value: 10000 },
    { date: "2025-02", value: 10500 }
  ],
  netComparison: {
    currentYear: [1000, 1200, 900],
    previousYear: [800, 950, 1000]
  }
}
```

---

## Dashboard.vue

``json
{
  userName: "Test User",
  netWorth: 15892.34,
  income: [
    {
      month: "May",
      amount: 4500
    },
    {
      month: "Apr",
      amount: 4700
    }
  ],
  spending: [
    { category: "Food", amount: 800 },
    { category: "Housing", amount: 1500 }
  ],
  transactions: [
    { date: "2025-05-30", description: "Coffee Shop", amount: -4.5, category: "Food" }
  ]
}
```

---

## Forecast.vue

``json
{
  forecastPeriods: ["2025-06", "2025-07", "2025-08"],
  incomeForecast: [
    { period: "2025-06", income: 5000 },
    { period: "2025-07", income: 5100 }
  ],
  expenseForecast: [
    { period: "2025-06", expense: 3200 },
    { period: "2025-07", expense: 3300 }
  ],
  adjustments: [
    { type: "add", category: "Freelance", amount: 500, period: "2025-07" }
  ]
}
```

---

## Investments.vue

```
{
  holdings: [
    { symbol: "AAPL", shares: 10, value: 1750.00 },
    { symbol: "TSLA", shares: 5, value: 1050.00 }
  ],
  performance: [
    { month: "2025-04", value: 5000 },
    { month: "2025-05", value: 5250 }
  ]
}
```

---

