# Financial Summary Detailed View

`frontend/src/views/FinancialSummaryDetailed.vue` stitches together the `DateRangeSelector`, `DailyNetChart`, and `FinancialSummary` components to provide a focused financial snapshot page.
The extended detail view also renders `frontend/src/components/statistics/DailySpendingPanel.vue` to surface the daily spending breakdown and latest transactions.

Key behaviors:

- Date range selections are forwarded to both the chart and summary so derived metrics include zero-value days across the chosen window.
- `DailyNetChart` emits padded `data-change` payloads; `FinancialSummary` uses the `startDate` and `endDate` props to align averages, moving averages, and volatility calculations with the padded range.
- The `summary-change` event from `DailyNetChart` drives the headline totals while the summary panel handles extended metrics (moving averages, trends, volatility) using the padded series.
- The extended detail view now includes a "Today's Spending" panel that loads a single-day category breakdown and recent transactions for the selected detail date.
