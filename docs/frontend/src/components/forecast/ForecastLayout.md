# ForecastLayout

## Purpose

`ForecastLayout` orchestrates forecast data loading, account scoping, and cross-component compute metadata for the summary, chart, breakdown, and adjustment form.

## Responsibilities

- Fetch forecast data through `useForecastData`.
- Load available forecast accounts and Dashboard Account Snapshot groups.
- Read typed aspect series from the forecast response for sidebar summaries and chart overlays.
- Build `forecastComputeMeta` so child components can describe the active lookback window, moving-average selection, normalization state, and auto-detected adjustment usage.

## Child metadata flow

- `ForecastSummaryPanel` receives `computeMeta` to keep tooltip copy aligned with the current forecast controls.
- `ForecastChart` receives `computeMeta` to populate the “How this forecast is calculated” methodology text.
- `ForecastChart` also receives the structured `series` map so it can render user-visible aspect
  overlays without reconstructing them from generic cashflow rows.

## Notes

- `forecastComputeMeta` prefers API metadata for lookback values and falls back to realized-history length when needed.
- Auto-detected adjustment metadata includes both explicit API adjustments and the derived baseline trend adjustment shown in the layout.
- The manual adjustments panel now reads the `manual_adjustments` series, while the realized-income
  panel reads the `realized_income` series emitted by the backend. The layout keeps `cashflows` available
  for backward compatibility but no longer depends on them to reconstruct user-visible aspect summaries.
