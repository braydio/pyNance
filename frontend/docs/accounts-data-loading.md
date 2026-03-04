# Accounts view data loading and retry behavior

This document describes how `frontend/src/views/Accounts.vue` and sparkline widgets load account summary,
transactions, and history data.

## Shared account history path

`useAccountHistory` is the single retrieval path for account balance history used by:

- `frontend/src/views/Accounts.vue` (Balance History chart)
- `frontend/src/components/widgets/AccountSparkline.vue` (balance/transaction toggle sparkline)

Both consumers read the same normalized `{ date, balance }` records from `useAccountHistory` for the same
account and date window contract. The Accounts chart uses the selected range, while sparklines use the
shared default `30d` range.

The composable owns the shared contract for all account-history consumers:

- payload normalization,
- date-range conversion,
- request caching and de-duplication,
- loading/error state.

## Sidebar refresh controls

The Accounts view renders `AccountActionsSidebar` in the `TabbedPageLayout` sidebar slot. This exposes
the "Refresh Plaid Accounts" panel, including the manual "Sync Account Activity" action used to run a
bulk Plaid account refresh from the Accounts page.

## Parallel loading model

The Accounts view uses a single `loadData()` function to request all account panels in parallel via
`Promise.all()`.

- `summary` uses `fetchNetChanges()`
- `transactions` uses `fetchRecentTransactions()`
- `history` uses `useAccountHistory().loadHistory()`

## Loading and error state policy

The view keeps one refresh state for summary/transactions and delegates history state to the composable.

- `loadingSummary` and `loadingTransactions` are view-level flags.
- `loadingHistory` and `historyError` come directly from `useAccountHistory`.
- Errors are panel-specific and attached through retry components.

## Retry policy

Retry actions are scoped by panel:

- Summary retry triggers `loadData()`.
- Transactions retry triggers `loadData()`.
- History retry triggers `loadHistory()` in the shared composable.

Top-level refresh buttons still request all three queries.

## Payload normalization

All account-history payload shape handling is centralized in `useAccountHistory`.

The composable normalizes known response variants into sorted `{ date, balance }` records so chart and
sparkline consumers operate on the same data model.
