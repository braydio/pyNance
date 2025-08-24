# Financial Summary Component

Renders key income and expense totals along with extended statistics such as moving averages, trend, volatility, highest income/expense days, and outlier detection.

## Props
- `summary` – object containing totals and above‑average day counts.
- `chartData` – daily net data used to derive extended statistics.
- `zoomedOut` – whether the parent chart is zoomed out; affects display of above‑average day counts.
- `defaultExtended` – if true, the extended statistics panel is shown initially.

## Related Views
- `FinancialSummaryDetailed.vue` displays this component with the extended panel enabled by default.

## Related API
- [`GET /api/summary/financial`](../backend/app/routes/summary.md)
