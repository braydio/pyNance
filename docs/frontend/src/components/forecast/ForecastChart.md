# ForecastChart

## Purpose

`ForecastChart` renders the forecast chart area, keeps the Month/Year toggle intact, and now switches between multiple forecast aspects without forcing the user off the current timeframe.

## Props

- `timeline`: Array of forecast timeline points, each containing `label`, `forecast_balance`, and `actual_balance`.
- `realizedHistory`: Historical balance points used for the balance overlay.
- `viewType`: Display mode (`Month` or `Year`).
- `graphMode`: Overlay mode (`combined`, `forecast`, or `historical`).
- `selectedAspect`: Active chart aspect (`balances`, `realized_income`, `manual_adjustments`, `spending`, or `debt`).
- `cashflows`: Forecast cashflow rows used to build income, manual-adjustment, and spending datasets.
- `assetBalance`, `liabilityBalance`, `netBalance`: Snapshot balances used by the debt-composition view.

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

- The chart title combines the current timeframe and active aspect so users can quickly confirm what they are viewing.
- Balance mode still overlays realized history with projected balances.
- Graph mode continues to control the balance overlay, while the aspect selector remains orthogonal for income, manual-adjustment, spending, and debt views so those series remain visible when users keep the same timeframe but change what is being visualized.
- Income, manual-adjustment, and spending modes rebuild datasets from forecast cashflows rather than relying on the original hard-coded two-line balance chart.
- Debt mode presents current asset, liability, and net snapshot lines for quick composition comparison.
- If the active aspect has no renderable data, the component renders a friendly empty-state message instead of the chart canvas.
