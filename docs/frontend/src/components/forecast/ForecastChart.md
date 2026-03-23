# ForecastChart

## Purpose

`ForecastChart` renders the forecast vs actual balance lines, overlays typed aspect series from the
forecast response, manages the Month/Year toggle UI, and exposes a compact explanation of the
compute settings behind the current projection.

## Props

- `timeline`: Array of forecast timeline points, each containing `label`, `forecast_balance`, and `actual_balance`.
- `realizedHistory`: Historical balance points rendered alongside forecast data.
- `viewType`: Display mode (`Month` or `Year`).
- `graphMode`: Chart mode (`combined`, `forecast`, or `historical`).
- `series`: Structured aspect series keyed by stable names such as `realized_income`,
  `manual_adjustments`, `spending`, and `debt_totals`.
- `computeMeta`: Forecast compute metadata from `ForecastLayout`, including lookback days, moving-average window, normalization state, and whether auto-detected adjustments were included.

## Events

- `update:viewType`: Emitted when the toggle button requests a new view type.

## Methodology help text

The compact “How this forecast is calculated” element summarizes:

- the realized-history lookback period used for the projection baseline,
- the moving-average window currently selected in the parent layout,
- whether normalization is on or off,
- the active graph mode shown in the chart, and
- whether auto-detected adjustments are currently included, including the detected count when available.

## Notes

- If the timeline is empty, the component renders a friendly empty-state message instead of the chart canvas.
- The methodology copy is driven entirely by parent metadata, so it updates whenever layout controls change and a recompute occurs.
- The chart now aligns all datasets on a unified date axis so balance lines and aspect overlays come
  directly from the backend’s typed `series` payload instead of inferred cashflow reconstructions.
