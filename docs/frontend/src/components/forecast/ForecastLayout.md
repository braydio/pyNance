# ForecastLayout

## Purpose

`ForecastLayout` orchestrates forecast data loading, account scoping, and cross-component compute metadata for the summary, chart, breakdown, and adjustment form.

## Responsibilities

- Fetch forecast data through `useForecastData`.
- Load available forecast accounts and Dashboard Account Snapshot groups.
- Read typed aspect series from the forecast response for sidebar summaries and chart overlays.
- Maintain an orthogonal chart aspect selector (`balances`, `realized_income`,
  `manual_adjustments`, `spending`, `debt`) so users can keep the same timeframe while changing
  what is visualized.
- Build `forecastComputeMeta` so child components can describe the active lookback window, moving-average selection, normalization state, and auto-detected adjustment usage.
- Render auto-detected adjustment drill-downs so users can inspect backend-provided `metadata.source_transactions` references for inferred wage and rent entries.

## Child metadata flow

- `ForecastSummaryPanel` receives `computeMeta` to keep tooltip copy aligned with the current forecast controls.
- `ForecastChart` receives `computeMeta` to populate the “How this forecast is calculated” methodology text.
- `ForecastChart` also receives the structured `series` map so it can render user-visible aspect
  overlays without reconstructing them from generic cashflow rows.

## Notes

- `forecastComputeMeta` prefers API metadata for lookback values and falls back to realized-history length when needed.
- Auto-detected adjustment metadata includes both explicit API adjustments and the derived baseline trend adjustment shown in the layout.
- Auto-detected adjustments are grouped by detection type in the UI so wage-income and rent-expense inferences are visually distinct while still sharing a common drill-down pattern.
- The manual adjustments panel now reads the `manual_adjustments` series, while the realized-income
  panel reads the `realized_income` series emitted by the backend.
- Auto-detected adjustment rows only show the drill-down toggle when source transactions are present; adjustments without sources render a passive empty-state message instead of an expandable panel.
