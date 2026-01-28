# ForecastChart

## Purpose

`ForecastChart` renders the forecast vs actual line chart and manages the Month/Year toggle UI.

## Props

- `timeline`: Array of forecast timeline points, each containing `label`, `forecast_balance`, and `actual_balance`.
- `viewType`: Display mode (`Month` or `Year`).

## Events

- `update:viewType`: Emitted when the toggle button requests a new view type.

## Notes

- If the timeline is empty, the component renders a friendly empty-state message instead of the chart canvas.
