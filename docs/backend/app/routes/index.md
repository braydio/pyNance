# backend/app/routes Documentation Index

This index catalogs the Flask blueprints defined under `backend/app/routes` and
links to the corresponding reference material. Routes are grouped by the
features they support so contributors can quickly find the relevant API surface.

---

## Table of Contents

### Dashboard & Insights

- [`dashboard.py`](dashboard.md) – Snapshot preferences and account group CRUD.
- [`summary.py`](summary.md) – Financial aggregates used on the dashboard.
- [`charts.py`](charts.md) – Time-series visualizations and chart helpers.
- [`forecast.py`](forecast.md) – Cash flow forecasting endpoints.
- [`arbitrage.py`](arbitrage.md) – Latest R/S arbitrage snapshot feed.
- [`arbit_dashboard.py`](arbit_dashboard.md) – Optional arbitrage dashboard APIs.

### Planning & Goals

- [`planning.py`](planning.md) – Budget planning (bills and allocations).
- [`goals.py`](goals.md) – Financial goal creation and listing.
- [`recurring.py`](recurring.md) – Scheduled transaction management.
- [`manual_io.py`](manual_io.md) – Manual import/export utilities for CSV files.

### Accounts & Transactions

- [`accounts.py`](accounts.md) – Account linking and lifecycle management.
- [`institutions.py`](institutions.md) – Institution aggregation and refresh.
- [`transactions.py`](transactions.md) – Core transaction queries and updates.
- [`categories.py`](categories.md) – Category metadata and tagging flows.
- [`product_transactions.py`](product_transactions.md) – Productized transaction exports.
- [`export.py`](export.md) – Bulk export helpers for downstream analysis.
- [`frontend.py`](frontend.md) – SPA entry point and static asset handling.

### Integrations & Sync

- [`plaid.py`](plaid.md) – Plaid link token exchange and item lifecycle.
- [`plaid_transactions.py`](plaid_transactions.md) – Plaid transaction sync APIs.
- [`plaid_investments.py`](plaid_investments.md) – Plaid investments data fetchers.
- [`plaid_transfer.py`](plaid_transfer.md) – Plaid transfer product orchestration.
- [`plaid_webhook.py`](plaid_webhook.md) – Webhook handlers for Plaid events.
- [`fidelity.py`](fidelity.md) – Fidelity integration wrapper.
- [`investments.py`](../../../../backend/app/routes/investments.py) – Investment accounts/holdings APIs.
- [`plaid_webhook_admin.py`](../../../../backend/app/routes/plaid_webhook_admin.py) – Administrative webhook utilities.

---

## Route Module Inventory

| Category                | Module                                                                              | Description                                                                                                     |
| ----------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Dashboard & Insights    | [`dashboard.py`](../../../../backend/app/routes/dashboard.py)                       | Account snapshot preferences and account group CRUD backed by `account_snapshot` and `account_groups` services. |
| Dashboard & Insights    | [`summary.py`](../../../../backend/app/routes/summary.py)                           | Daily aggregate income/expense metrics with trend and outlier analytics.                                        |
| Dashboard & Insights    | [`charts.py`](../../../../backend/app/routes/charts.py)                             | Chart data assembly for balance trends and breakdowns.                                                          |
| Dashboard & Insights    | [`forecast.py`](../../../../backend/app/routes/forecast.py)                         | Forecasted cash flow projections.                                                                               |
| Dashboard & Insights    | [`arbitrage.py`](../../../../backend/app/routes/arbitrage.py)                       | Reads the Discord-exported arbitrage snapshot from disk.                                                        |
| Dashboard & Insights    | [`arbit_dashboard.py`](../../../../backend/app/routes/arbit_dashboard.py)           | Supplemental arbitrage dashboards enabled by feature flag.                                                      |
| Planning & Goals        | [`planning.py`](../../../../backend/app/routes/planning.py)                         | CRUD for planned bills and allocation targets via `planning_service`.                                           |
| Planning & Goals        | [`goals.py`](../../../../backend/app/routes/goals.py)                               | Manage `FinancialGoal` records for long-term objectives.                                                        |
| Planning & Goals        | [`recurring.py`](../../../../backend/app/routes/recurring.py)                       | Manage recurring transaction templates.                                                                         |
| Planning & Goals        | [`manual_io.py`](../../../../backend/app/routes/manual_io.py)                       | Manual CSV import/export flows for accounts and transactions.                                                   |
| Accounts & Transactions | [`accounts.py`](../../../../backend/app/routes/accounts.py)                         | Account lifecycle management, including Plaid link orchestration.                                               |
| Accounts & Transactions | [`institutions.py`](../../../../backend/app/routes/institutions.py)                 | Aggregated institution payloads and Plaid refresh coordination.                                                 |
| Accounts & Transactions | [`transactions.py`](../../../../backend/app/routes/transactions.py)                 | Core transaction CRUD, filters, and enrichment triggers.                                                        |
| Accounts & Transactions | [`categories.py`](../../../../backend/app/routes/categories.py)                     | Category taxonomy reads and writes.                                                                             |
| Accounts & Transactions | [`product_transactions.py`](../../../../backend/app/routes/product_transactions.py) | Productized/curated transaction downloads.                                                                      |
| Accounts & Transactions | [`export.py`](../../../../backend/app/routes/export.py)                             | CSV/Excel export surfaces for accounts and transactions.                                                        |
| Accounts & Transactions | [`frontend.py`](../../../../backend/app/routes/frontend.py)                         | Serves the Vue single-page application shell.                                                                   |
| Integrations & Sync     | [`plaid.py`](../../../../backend/app/routes/plaid.py)                               | Plaid item and link token lifecycle management.                                                                 |
| Integrations & Sync     | [`plaid_transactions.py`](../../../../backend/app/routes/plaid_transactions.py)     | Transaction sync orchestration with Plaid.                                                                      |
| Integrations & Sync     | [`plaid_investments.py`](../../../../backend/app/routes/plaid_investments.py)       | Fetch Plaid investments holdings and transactions.                                                              |
| Integrations & Sync     | [`plaid_transfer.py`](../../../../backend/app/routes/plaid_transfer.py)             | Initiate and monitor Plaid transfer workflows.                                                                  |
| Integrations & Sync     | [`plaid_webhook.py`](../../../../backend/app/routes/plaid_webhook.py)               | Webhook handlers for Plaid item and transaction updates.                                                        |
| Integrations & Sync     | [`plaid_webhook_admin.py`](../../../../backend/app/routes/plaid_webhook_admin.py)   | Admin endpoints for replaying Plaid webhook payloads.                                                           |
| Integrations & Sync     | [`investments.py`](../../../../backend/app/routes/investments.py)                   | REST surface for investment accounts, holdings, and transactions.                                               |
| Integrations & Sync     | [`fidelity.py`](../../../../backend/app/routes/fidelity.py)                         | Bridge to the Fidelity scraping service for investment accounts.                                                |

The table reflects the current file inventory; consult individual markdown pages
for deeper request/response details and service cross-references.
