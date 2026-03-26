# ForecastSummaryPanel

## Purpose

`ForecastSummaryPanel` displays the current balance context, manual income/liability controls, and account-selection shortcuts that scope forecast recomputes.

## Props

- `assetBalance`: Included asset-account total used as the positive side of the starting balance.
- `liabilityBalance`: Included liability-account total used as the negative side of the starting balance.
- `netBalance`: Current starting balance shown as assets minus liabilities for the selected account scope.
- `manualIncome`: Manual daily income adjustment value.
- `liabilityRate`: Manual daily liability adjustment value. The compute payload now classifies this
  control as debt growth from new spending so backend debt series do not treat it as generic
  liability drift.
- `netChange`: Computed net delta returned by the forecast API when available.
- `viewType`: Current view mode (`Month` or `Year`).
- `accountGroupOptions`: Dashboard Account Snapshot groups exposed as quick-select account shortcuts.
- `computeMeta`: Forecast compute metadata passed from `ForecastLayout`, including lookback days, moving-average window, normalization state, and auto-detected adjustment counts.

## Events

- `update:manualIncome`: Emitted when the manual income input changes.
- `update:liabilityRate`: Emitted when the liability input changes.
- `update:includedAccountIds`: Emitted when include scope changes.
- `update:excludedAccountIds`: Emitted when exclude scope changes.

## Tooltip meanings

- `Assets`: Explains that the value totals included asset/positive-balance accounts and reminds users they can click the value to review scoped accounts.
- `Liabilities`: Explains that the value totals included debt balances that offset the starting position.
- `Current Balance`: Explains that the displayed starting balance is assets minus liabilities before any projected cashflow changes.
- `Manual Income`: Explains that the input adds a daily manual income amount to each forecasted day and reflects the current control value.
- `Liability Rate`: Explains that the input subtracts a daily manual liability amount from each forecasted day, classifies it as manual debt growth from new spending, and reflects the current control value.
- `Net Delta`: Explains whether the displayed delta comes from computed forecast output or a fallback of manual income minus liability rate, and references the active moving-average/lookback settings when available.

## Account Selector

- The balance values are clickable and open an account contribution selector panel.
- The selector supports account-level include and exclude toggles and emits:
  - `update:includedAccountIds`
  - `update:excludedAccountIds`
- Layout/composable integrations use these toggles to recompute forecast outputs with scoped account sets.

## Dashboard Group Integration

- Quick-select chips mirror configured Dashboard Account Snapshot groups so forecast users can apply the same grouping context without manually re-selecting each account.
- Applying a group shortcut emits `update:includedAccountIds` with that group's account IDs and clears `update:excludedAccountIds` to keep selection intent explicit.
