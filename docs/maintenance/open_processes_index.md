# 📌 Open Processes & Planning Index

This document consolidates active development plans across the repository so they are easy to locate. Each section references the original planning file that contains more detail.

## Forecast Engine

- **Docs:** `docs/forecast/FORECAST_ROADMAP.md`, `docs/BACKEND_STATUS.md`
- Integrate `transactions`, `account_history`, and `recurring_transactions` into forecasting logic.
- Implement delta analysis, input validation, and additional analytics.
- Complete frontend wiring for live forecast data.

## Recurring Transactions & Notifications

- **Docs:** `docs/CODEX_REPORT.md`
- Validate recurring rule edits and provide confirmation dialogs.
- Add pattern detection and simulate upcoming instances.

## Investments & Liabilities Sync

- **Docs:** `docs/organize/routing_refactor/Investments_Integration-Summary_Overview.md`
- Create `routes/product_investments.py` and `services/investments.py`.
- Implement Plaid `/investments` calls and register the new route.

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
