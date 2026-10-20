# Transactions Table Summaries and Filter Scope

Packet: TP-20261019-002. Applies to the Activity table on `/transactions`.

The table shows **one page** of rows. Everything else on the page (the match count, the totals, the CSV
export) describes **all rows that match the active filters**. The two are never mixed in one number.

## One filter set

Every control that narrows the table ends up in a single canonical filter object, owned by
`useTransactions` (`queryFilters`) and keyed by `filterHash`:

| Control | Request parameter |
| --- | --- |
| Period / date range | `start_date`, `end_date` |
| Account | `account_ids` |
| Type | `tx_type` (`credit` = stored amount > 0, `debit` = stored amount < 0; Plaid stores money out as positive) |
| Search box | `search` (debounced 300 ms; empty clears immediately) |
| Column filters (Date, Description, Merchant, Account, Institution, Category) | `filter_date`, `filter_description`, `filter_merchant_name`, `filter_account_name`, `filter_institution_name`, `filter_category` |
| Category / subcategory selects | `category_primary` (prefix match), `category_sub` (contains) |
| Sort select | `sort` (orders rows only; does not change totals) |
| Transfers | `include_transfers` (default off, same as the table) |

The same parameters feed:

- `GET /api/transactions/get_transactions`: page rows and the matching `total`.
- `GET /api/transactions/summary`: totals over all matching rows.
- CSV export: pages through `get_transactions` with these parameters. There is no client-side re-filtering.

The backend owns the semantics in `account_logic.build_transaction_filter_query`, so the page, its count and the
summary are built from the same relation. Text matching is case-insensitive substring, bound as parameters, with `%`
and `_` treated literally. `search` matches transaction id, date, description, merchant, account, institution and
category. Free-text queries are not cached.

The table component runs with `server-filtered`: it neither narrows nor re-slices the rows it receives. It reports its
column and category filters through `update:filters`, and the view merges them into the canonical set. A standalone
table (without `server-filtered`) still filters its loaded rows locally and is a loaded-page view only.

## The summary endpoint

`GET /api/transactions/summary` takes the filter parameters above (paging and sort are ignored) and returns:

```json
{
  "scope": "all_matching",
  "matching_count": 51,
  "income": 1000, "expenses": -300, "refunds": 25, "economic_net": 725,
  "transfers_in": 0, "transfers_out": 0, "debt_settlements": 131.64,
  "investment_movements": 0, "unclassified_in": 100, "unclassified_out": 0,
  "needs_review_count": 1, "pending_excluded_count": 0,
  "breakdowns": { "by_category": [], "by_account": [], "by_month": [] },
  "latest_transaction_date": "2026-10-13", "as_of": "...", "applied_filters": {}
}
```

- Classification is the shared `transaction_flow_classification` (`classify_rows`), run once per row with a single
  batched counterpart lookup. Only income, expense and refund rows are economic.
- `expenses` is negative, `refunds` is a separate positive adjustment, and
  `economic_net = income + expenses + refunds`.
- Transfers, debt settlements, investment movement and unclassified rows are reported beside the economic figures and
  never inside `economic_net`. Rows with no usable sign or classification are counted in `needs_review_count`, never
  defaulted to income.
- Breakdowns cover economic rows only and each one sums to the headline figures.
- The endpoint is bound to the trusted server owner (`PYNANCE_OWNER_USER_ID`) and returns 503 without one. Hidden
  accounts, other owners' rows and pending rows are excluded; `pending_excluded_count` says how many matching pending
  rows were left out, so the table total can be reconciled with `matching_count`.
- Read-only. No schema change, no external service.

## What the page shows

- **Filtered results · N matches**: Economic income (excl. transfers), Economic expenses, Refund adjustments, Economic
  net. These come from the summary and do not change with page or sort.
- **Page X of Y · N shown**: with **Cash movement (current page)**, the signed sum of the rows actually rendered
  (money out is negative). It is not income or net. Placeholder rows are not counted.
- A disclosure lists transfers, debt payments, investment movement, unreviewed amounts, rows needing review and
  pending rows that were not counted.
- If totals fail to load the panel says **Totals unavailable** with a Retry button; it never shows zeros for an error.
  If a refresh fails for filters that already had values, those values stay, marked stale. After a filter change
  the previous values are dropped.

The totals panel appears when any filter, search term or column filter is active. Responses are keyed by the summary
filter hash, so a slow answer for earlier filters cannot overwrite the current ones. Editing a transaction or
confirming/unmarking a transfer refreshes the totals.

## Page rows

`useTransactions` keeps server pages by number (`currentPageRows`), so jumping to page 5 does not depend on pages 2-4
being loaded. Search and filters are applied by the server; the loaded-page client sort only orders the visible page.
Use the Sort select for an order across all matching rows.
