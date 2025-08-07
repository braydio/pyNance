# Daily Net Chart Design

This component renders a daily summary of income and expenses using stacked bars with a net line overlay. To emphasize cash flow, expense values are stored as negatives so that red bars extend **below** the X‑axis while green income bars remain above it.

The chart emits a `bar-click` event with the associated date whenever a bar is clicked. See [DASHBOARD_MODAL_GUIDE.md](./DASHBOARD_MODAL_GUIDE.md) for how these events open the transaction modal.
