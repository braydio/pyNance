# ForecastSummaryPanel

## Purpose

`ForecastSummaryPanel` displays the current balance along with manual income and liability inputs used to adjust forecasts.

## Props

- `currentBalance`: Starting balance for the forecast window.
- `manualIncome`: Manual income adjustment value.
- `liabilityRate`: Manual liability adjustment value.
- `viewType`: Current view mode (`Month` or `Year`).
- `accountGroupOptions`: Dashboard Account Snapshot groups exposed as quick-select account shortcuts.

## Events

- `update:manualIncome`: Emitted when the manual income input changes.
- `update:liabilityRate`: Emitted when the liability input changes.

## Notes

- The panel surfaces a simple net delta hint based on the two manual inputs.

## Account Selector

- The current balance value is clickable and opens an account contribution selector panel.
- The selector supports account-level include and exclude toggles and emits:
  - `update:includedAccountIds`
  - `update:excludedAccountIds`
- Layout/composable integrations use these toggles to recompute forecast outputs with scoped account sets.

## Dashboard Group Integration

- Quick-select chips mirror configured Dashboard **Account Snapshot** groups so forecast users can apply the same grouping context without manually re-selecting each account.
- Applying a group shortcut emits `update:includedAccountIds` with that group's account IDs and clears `update:excludedAccountIds` to keep selection intent explicit.
