# Dashboard chart components

This reference covers the three chart components currently rendered on the dashboard so changes to their behavior or styles can be tracked alongside the documentation requirements enforced by the githooks.

## AccountBalanceHistoryChart

- **File:** `frontend/src/components/charts/AccountBalanceHistoryChart.vue`
- **Purpose:** Renders a line chart of account balances over time. It listens for updates to `historyData` and `selectedRange`, re-rendering with a transition key so the `<canvas>` is replaced and the new Chart.js instance is tied to the current dataset.
- **Key behaviors:**
  * Normalizes each transaction row via `formatCategory` in the `useTransactions` composable so the chart stays in sync with cached pagination.
  * Guards Chart.js initialization by waiting for `nextTick()` and ensuring the canvas exists before calling `ctx.getContext('2d')`, then destroys any previous chart instance before configuring a new `line` chart.
- **Props:**
  * `historyData` (`Array`): Time-series balance points.
  * `selectedRange` (`String`): Controls animation timing and optional forced re-rendering.

## NetIncomeCharts

- **File:** `frontend/src/components/charts/NetIncomeCharts.vue`
- **Purpose:** Displays grouped net income bars (positive/negative) for daily/weekly/monthly breakdowns. The component fetches cash-flow data via `api.fetchCashFlow` and updates the Chart.js instance with gradients that depend on the active canvas height.
- **Key behaviors:**
  * Rebuilds gradients and the chart after each data fetch or granularity change while guarding against missing canvas refs.
  * Calculates summary values (`totalIncome`, `totalExpenses`, `totalNet`) that feed the adjacent statistics display.
  * Provides controls for switching granularity (`daily`, `weekly`, `monthly`) that re-fetch data.

## PortfolioAllocationChart

- **File:** `frontend/src/components/charts/PortfolioAllocationChart.vue`
- **Purpose:** Renders a doughnut chart describing the allocation of the user's portfolio. Inputs are an array of `{ label, value }` objects where each label maps to a data slice and per-slice colors are generated from the accent palette.
- **Key behaviors:**
  * Uses `getAccentColor()` to keep the palette in sync with the rest of the UI.
  * Rebuilds the Chart.js instance whenever `allocations` change, safely destroying the existing chart before creating a new doughnut configuration.
  * Ensures the canvas element is present before calling `ctx.getContext('2d')` to avoid Chart.js errors when the component renders on the server or during rapid navigation.

Including these references satisfies the documentation linter by making the component paths discoverable inside `docs/frontend`.
