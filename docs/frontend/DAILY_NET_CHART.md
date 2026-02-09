# Daily Net Chart Design

This component renders a daily summary of income and expenses using stacked bars with a net line overlay. To emphasize cash flow, expense values are stored as negatives so that red bars extend **below** the X‑axis while green income bars remain above it.

By default the chart displays every day in the selected month, including future dates in the current month. Days without data are padded with zeroed income/expense/net values so the X-axis remains complete, while tooltip summaries and dashboard totals continue to reflect month-to-date activity.

The chart emits a `bar-click` event with the associated date whenever a bar is clicked. See [DASHBOARD_MODAL_GUIDE.md](./DASHBOARD_MODAL_GUIDE.md) for how these events open the transaction modal.

## Comparison Overlay

The dashboard overlay sidebar now supports a comparison series that fetches a prior-period dataset from
`/api/charts/daily_net` and aligns it to the current chart labels. Two modes are supported:

- **Prior month to-date** aligns the previous month's daily net values by day-of-month.
- **Last 30 days vs previous 30** aligns the prior 30-day period by day index.

The comparison series renders as a faint, dashed line so it is visible without overpowering the primary
income and expense bars.

## Loading, Empty, and Error States

The chart now manages explicit request/UI state with local reactive flags:

- `isLoading`: shows an inline loading state while primary or comparison requests are in flight.
- `isEmpty`: displays "No transactions found for the selected date range." when the resolved daily series has no transactional activity for the selected window.
- `hasError`: shows an error banner with a retry action when either API request fails or returns a non-success status.

When `hasError` or `isEmpty` is active, chart rendering is deferred and the canvas/legend are hidden to avoid stale visuals.
