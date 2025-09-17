# 📌 Open Processes & Planning Index

This document consolidates active development plans across the repository so they are easy to locate. Each section references the canonical planning file that contains more detail.

## Accounts Experience

- **Docs:** `docs/roadmaps/accounts.md`
- Finish the dedicated history chart, add range presets, and annotate large balance swings.
- Instrument `/api/accounts/<id>/history` for latency/error metrics and extend unit/integration coverage.

## Transactions Sync Hardening

- **Docs:** `docs/roadmaps/transactions.md`
- Add focused tests for Plaid delta-sync (duplicate cursors, removed transactions, error propagation).
- Emit sync metrics and document replay/backfill procedures for operations.

## Planning & Allocations

- **Docs:** `docs/roadmaps/planning.md`
- Ship the planning components (`BillForm`, `BillList`, `Allocator`, `PlanningSummary`) with optimistic UI flows.
- Transition the Flask planning routes from in-memory storage to persistent models and enforce allocation caps end-to-end.

## Investments & Liabilities Sync

- **Docs:** `docs/roadmaps/investments.md`
- Harden webhook-triggered refreshes with tests and metrics; capture Plaid identifiers in logs.
- Build allocation/performance dashboards and export tooling on the frontend.

## Forecast Engine

- **Docs:** `docs/forecast/FORECAST_ROADMAP.md`, `docs/BACKEND_STATUS.md`
- Integrate `transactions`, `account_history`, and `recurring_transactions` into forecasting logic.
- Implement delta analysis, input validation, and additional analytics.
- Complete frontend wiring for live forecast data.

## Recurring Transactions & Notifications

- **Docs:** `docs/CODEX_REPORT.md`
- Validate recurring rule edits and provide confirmation dialogs.
- Add pattern detection and simulate upcoming instances.

## Routing Refactor

- **Docs:** `docs/CODEX_REPORT.md`, `docs/organize/routing_refactor/TxRoutes/`
- Finish `services/transactions.py` and migrate legacy logic.
- Apply shared middleware and deprecate old routes.

## Account Link Flow Improvements

- **Docs:** `2025-05-17_pyNance_account_link_flow_refactor.md`
- Trigger link token generation on demand and improve product selection UX.

## Frontend UI Tasks

- **Docs:** `docs/frontend/Consolidated_TODO.md`
- Address styling and functionality gaps in Dashboard components and tables.

## Repository Cleanup

- **Docs:** `docs/maintenance/cleanup_checklist.md`
- Consolidate legacy docs, organize mapping files, and ensure test directories exist.
