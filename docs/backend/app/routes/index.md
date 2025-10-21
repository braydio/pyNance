# backend/app/routes Documentation Index

This index tracks every module under `backend/app/routes/` and points to
their dedicated documentation. Use the grouped sections below to jump to
functional areas or open the detailed Markdown pages for request/response
shape references.

---

## Account & Institution Management

- [`accounts.py`](accounts.md) – lifecycle management for linked financial accounts.
- [`dashboard.py`](dashboard.md) – account snapshot preferences and custom account groups backed by `app.services.account_snapshot` and `app.services.account_groups`.
- [`institutions.py`](institutions.md) – institution rollups, refresh triggers, and Plaid-backed sync helpers.
- [`manual_io.py`](manual_io.md) – manual cashflow ingestion utilities for non-aggregated accounts.
- [`recurring.py`](recurring.md) – CRUD endpoints for recurring transactions and reminders.

## Transactions & Reporting

- [`categories.py`](categories.md) – transaction categorisation flows.
- [`charts.py`](charts.md) – aggregated chart feeds for UI visualisations.
- [`export.py`](export.md) – CSV exports for accounts and transactions.
- [`forecast.py`](forecast.md) – cashflow projections and budget forecasts.
- [`product_transactions.py`](product_transactions.md) – grouped transactions by fintech product source.
- [`summary.py`](summary.md) – income/expense rollups calculated directly from SQLAlchemy queries.
- [`transactions.py`](transactions.md) – primary transaction ledger APIs.
- [`rules.py`](rules.md) – automation rules that post-process imported transactions.

## Planning & Goals

- [`planning.py`](planning.md) – bill schedules and allocation targets leveraging `app.services.planning_service`.
- [`goals.py`](goals.md) – REST endpoints over the `FinancialGoal` ORM model for savings targets.

> Related: dashboard account grouping endpoints (see [`dashboard.py`](dashboard.md)) support planning widgets by controlling
> the snapshot composition shown to users.

## Investments & Brokerage

- [`investments.py`](investments.md) – holdings, transactions, and Plaid investment account utilities.
- [`fidelity.py`](fidelity.md) – direct integration with `app.services.fidelity_service.FidelityService` for brokerage data.
- [`plaid_investments.py`](plaid_investments.md) – Plaid investment synchronisation helpers.

## Plaid & External Integrations

- [`plaid.py`](plaid.md) – core Plaid link/token flows.
- [`plaid_transactions.py`](plaid_transactions.md) – transaction import callbacks and reconciliation.
- [`plaid_transfer.py`](plaid_transfer.md) – ACH transfer initiation and status polling.
- [`plaid_webhook.py`](plaid_webhook.md) – webhook receiver used by Plaid products.
- [`plaid_webhook_admin.py`](plaid_webhook_admin.md) – administrative endpoints for updating Plaid webhook targets.

## Dashboards & Frontend Utilities

- [`arbit_dashboard.py`](arbit_dashboard.md) – experimental arbitrage dashboard feeds.
- [`arbitrage.py`](arbitrage.md) – standalone endpoint returning the current arbitrage file contents.
- [`frontend.py`](frontend.md) – static asset serving helpers for the Vue client.

---

> ℹ️ Looking for docs on a specific endpoint? Each linked Markdown file contains
> a breakdown of supported routes, expected payloads, and references to the
> services or SQL helpers that supply the data.
