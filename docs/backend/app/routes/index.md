---
Owner: Backend Team
Last Updated: 2025-11-24
Status: Active
---

# Routes Documentation Index

## Purpose
Provide a consolidated map of Flask blueprints under `backend/app/routes` with quick links to detailed references.

## Endpoints
- Documentation-only index; see linked route docs for specific endpoints.

## Inputs/Outputs
- **Documentation access**
  - **Inputs:** None.
  - **Outputs:** Links to per-route references grouped by functional area.

## Auth
- Not applicable; this file is for documentation navigation.

## Dependencies
- Relies on individual route docs to describe behavior and contracts.

## Behaviors/Edge Cases
- Groupings reflect current blueprints; update when new routes are added or removed to keep navigation accurate.

## Sample Request/Response
```text
Use the links below to open a specific route reference.
```

### Dashboard & Insights
- [dashboard.md](dashboard.md) – Snapshot preferences and account group CRUD.
- [summary.md](summary.md) – Financial aggregates used on the dashboard.
- [charts.md](charts.md) – Time-series visualizations and chart helpers.
- [forecast.md](forecast.md) – Cash flow forecasting endpoints.

### Planning & Goals
- [planning.md](planning.md) – Bill planning and allocations.
- [goals.md](goals.md) – Financial goal creation and listing.
- [recurring.md](recurring.md) – Scheduled transaction management.
- [manual_io.md](manual_io.md) – Manual transaction entry endpoints.

### Accounts & Transactions
- [accounts.md](accounts.md) – Account lifecycle and categorization routes.
- [institutions.md](institutions.md) – Institution aggregation and refresh.
- [transactions.md](transactions.md) – Core transaction queries and updates.
- [categories.md](categories.md) – Category metadata and tagging flows.
- [export.md](export.md) – Bulk export helpers for downstream analysis.
- [frontend.md](frontend.md) – Frontend configuration delivery.

### Integrations & Sync
- [plaid_transactions.md](plaid_transactions.md) – Plaid transaction sync APIs.
- [plaid_investments.md](plaid_investments.md) – Plaid investments data fetchers.
- [plaid_webhook.md](plaid_webhook.md) – Webhook handlers for Plaid events.
