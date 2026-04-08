# Financial Summary Detailed View

`frontend/src/views/FinancialSummaryDetailed.vue` stitches together the `DateRangeSelector`, `DailyNetChart`, and `FinancialSummary` components to provide a focused financial snapshot page.
The extended detail view also renders `frontend/src/components/statistics/DailySpendingPanel.vue` to surface the daily spending breakdown and latest transactions.

Key behaviors:

- Date range selections are forwarded to both the chart and summary so derived metrics include zero-value days across the chosen window.
- `DailyNetChart` emits padded `data-change` payloads; `FinancialSummary` uses the `startDate` and `endDate` props to align averages, moving averages, and volatility calculations with the padded range.
- The `summary-change` event from `DailyNetChart` drives the headline totals while the summary panel handles extended metrics (moving averages, trends, volatility) using the padded series.
- The extended detail view now includes a "Today's Spending" panel that loads a single-day category breakdown and recent transactions for the selected detail date.
- The extended detail view now includes an "Upcoming Transactions" subsection that merges recurring reminders from selected snapshot accounts and ranks them by recurrence confidence plus observed occurrence count, so stronger auto-detected patterns appear first.
- When **Compare to average profile** is enabled, chart hover tooltips now provide profile-aware details for each stacked category segment, including the segment amount, share-of-profile percentage, and total stack value for that profile.
