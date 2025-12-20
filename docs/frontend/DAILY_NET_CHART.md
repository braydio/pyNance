# Daily Net Chart Design

This component renders a daily summary of income and expenses using stacked bars with a net line overlay. To emphasize cash flow, expense values are stored as negatives so that red bars extend **below** the X‑axis while green income bars remain above it.

By default the chart displays every day in the selected month, including future dates in the current month. Days without data are padded with zeroed income/expense/net values so the X-axis remains complete, while tooltip summaries and dashboard totals continue to reflect month-to-date activity.

The chart emits a `bar-click` event with the associated date whenever a bar is clicked. See [DASHBOARD_MODAL_GUIDE.md](./DASHBOARD_MODAL_GUIDE.md) for how these events open the transaction modal.
