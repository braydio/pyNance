# ForecastChart

## Purpose

`ForecastChart` renders the forecast vs actual balance lines, overlays typed aspect series from the
forecast response, manages the Month/Year toggle UI, and exposes a compact explanation of the
compute settings behind the current projection while letting users switch aspects without changing
the current timeframe.

## Props

- `timeline`: Array of forecast timeline points, each containing `label`, `forecast_balance`, and `actual_balance`.
- `realizedHistory`: Historical balance points used for the balance overlay.
- `viewType`: Display mode (`Month` or `Year`).
- `graphMode`: Chart mode (`combined`, `forecast`, or `historical`).
- `series`: Structured aspect series keyed by stable names such as `realized_income`,
  `manual_adjustments`, `spending`, `debt_totals`, `debt_interest`, and `debt_new_spending`.
- `computeMeta`: Forecast compute metadata from `ForecastLayout`, including lookback days, moving-average window, normalization state, and whether auto-detected adjustments were included.
- `selectedAspect`: Active chart aspect (`balances`, `realized_income`, `manual_adjustments`, `spending`, or `debt`).
- `cashflows`: Forecast cashflow rows preserved for compatibility with parent callers.
- `assetBalance`, `liabilityBalance`, `netBalance`: Snapshot balances used only as a fallback when the backend debt series are unavailable.

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
- The chart title combines the current timeframe and active aspect so users can quickly confirm what they are viewing.
- Balance mode still overlays realized history with projected balances.
- Graph mode continues to control the balance overlay, while the aspect selector remains orthogonal for income, manual-adjustment, spending, and debt views so those series remain visible when users keep the same timeframe but change what is being visualized.
- Income, manual-adjustment, and spending modes read directly from the backend’s typed series payload instead of reconstructing those datasets from generic cashflow rows.
- Debt mode now prioritizes the backend’s debt series contract so the chart can render projected
  total debt alongside daily debt-interest and debt-new-spending components.
- If the active aspect has no renderable data, the component renders a friendly empty-state message instead of the chart canvas.
