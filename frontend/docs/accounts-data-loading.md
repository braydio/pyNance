# Accounts view data loading and retry behavior

This document describes how `frontend/src/views/Accounts.vue` loads account summary, transactions,
and history data.

## Sidebar refresh controls

The Accounts view renders `AccountActionsSidebar` in the `TabbedPageLayout` sidebar slot. This exposes
the "Refresh Plaid Accounts" panel, including the manual "Sync Account Activity" action used to run a
bulk Plaid account refresh from the Accounts page.

## Parallel loading model

The Accounts view uses a single `loadData()` function to request all account panels in parallel via
`Promise.allSettled()`.

- `summary` uses `fetchNetChanges()`
- `transactions` uses `fetchRecentTransactions()`
- `history` uses `fetchAccountHistory()`

Because `Promise.allSettled()` is used, one failure does not block successful panels from rendering.

## Loading and error state policy

The view keeps one global refresh state (`isRefreshing`) and derives panel loading flags from
request status entries.

- `loadingSummary`, `loadingTransactions`, and `loadingHistory` are synchronized from
  `requestStatus` while a refresh is active.
- Errors are panel-specific and attached through `applyRequestState()`.

## Retry policy

Retry actions are scoped by panel:

- Summary retry triggers only the summary request.
- Transactions retry triggers only the transactions request.
- History retry triggers only the history request.

Top-level refresh buttons still request all three queries.

## Debounce behavior

When account selection or range changes rapidly, refresh calls are debounced (250 ms) to prevent
request bursts and stale response churn.

## Payload normalization

All API payload shape handling is centralized in parser helpers:

- `parseSummaryPayload()`
- `parseTransactionsPayload()`
- `parseHistoryPayload()`

This keeps response-shape branching out of template and call sites.
