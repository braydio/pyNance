
# 📊 Forecast Engine & Graph Specification

## 🧠 Overview: How Forecasting Works

The forecast system overlays projected financial data with historical performance to provide a net financial trajectory. The forecast engine uses actual Plaid data, inferred recurring items, and manual user adjustments.

---

## 🔁 Forecast Generation Logic

### 🔍 Data Sources

- **Plaid Transactions** – Historical income/expenses
- **Linked Investments** – Performance trends and growth
- **Account Balances** – Net worth tracking
- **Manual Inputs** – Income, liabilities, adjustments from user UI

### 🧮 Forecast Model

- **Recurring Entries**:
  - Forecasted based on recurrence rules and categories
  - Includes rent, bills, subscriptions, salaries, etc.
- **Investment Forecasts**:
  - Optional inclusion of monthly or compounded yield
- **Manual Overrides**:
  - From `ForecastAdjustmentsForm.vue`
  - Inputs like `manualIncome`, `liabilityRate`
- **Temporal Scope**:
  - Forecasts generated up to the end of the selected view (month/year)
- **Deprecation Logic**:
  - Adjusted based on granularity and frequency (e.g. annual amounts prorated monthly)

---

## ✅ Actuals Calculation

- Based on synced balances from Plaid and linked institutions
- Aggregates historical cash flow via `Transaction` and `AccountHistory`
- Sums real transaction amounts by date to match forecast intervals
- Actuals line always ends at “today”; does not extend into the future

---

## 🗓 View Modes and Toggle

### Modes

| View     | X-Axis         | Granularity  |
|----------|----------------|--------------|
| Month    | 1st → End of Month | Daily/Weekly |
| Year     | Jan 1st → Dec 31st | Monthly      |

### Toggle Behavior

- A toggle button switches between Month/Year views
- Affects:
  - Forecast generation scope
  - Actuals range
  - X-axis tick marks and formatting
  - Breakdown calculations
  - Recurring entry distribution logic

---

## 🔢 Recurring Entry Deprecation Logic

### Monthly Recurrence

- **Example**: $10/month
  - **Month View**: Pro-rate based on remaining days
  - **Year View**: $10 × months remaining

### Annual Recurrence

- **Example**: $120/year starting in June
  - **Year View**: Spread $120 over remaining months (e.g., $20/month)
  - **Month View (June)**: Show prorated share for June

### Breakdown Totals

- All recurring and manual entries are distributed over the forecast range
- Updated dynamically based on view mode

---

## 📈 Chart Rendering Features

- Two primary lines: **Forecasted** and **Actual**
- Based on real dates (x-axis)
- Forecast extends full duration of selected view
- Actual line stops at today
- Hover tooltips show date + value
- Breakdown sidebar updates per view toggle
- Toggle control in header

---

## 🧱 Engine & Component Structure

### 🧩 `useForecastEngine.ts` (Composable Module)

Exports:
```ts
getForecastData(viewType, forecastItems, manualIncome, liabilityRate): ForecastPoint[]
getActualsData(viewType): ForecastPoint[]
