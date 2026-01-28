# ForecastSummaryPanel

## Purpose

`ForecastSummaryPanel` displays the current balance along with manual income and liability inputs used to adjust forecasts.

## Props

- `currentBalance`: Starting balance for the forecast window.
- `manualIncome`: Manual income adjustment value.
- `liabilityRate`: Manual liability adjustment value.
- `viewType`: Current view mode (`Month` or `Year`).

## Events

- `update:manualIncome`: Emitted when the manual income input changes.
- `update:liabilityRate`: Emitted when the liability input changes.

## Notes

- The panel surfaces a simple net delta hint based on the two manual inputs.
