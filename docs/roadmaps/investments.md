# Investments Roadmap

## Snapshot

- Holdings, securities, and investment transactions are modelled via SQLAlchemy and refreshed through `upsert_investments_from_plaid` / `upsert_investment_transactions`.
- `/api/plaid/investments/refresh` (single item) and `/api/plaid/investments/refresh_all` (broadcast) trigger refreshes; `/api/investments` exposes read endpoints consumed by the Vue client.
- Plaid webhooks for `INVESTMENTS_TRANSACTIONS` and `HOLDINGS` are routed through `/api/webhooks/plaid`, enabling automatic updates.
- `/api/investments/transactions` now accepts filters for account, security, type, subtype, and ISO date ranges so analytics views can request scoped datasets without client-side filtering.

## Progress update (2025-09-17)

| Theme                          | Status         | Notes                                                                                                                                                                                |
| ------------------------------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Backend reliability & coverage | 🚧 In progress | API filtering has been hardened with server-side validation for type/subtype and date ranges. Webhook-driven tests and instrumentation for refresh timings remain to be implemented. |
| Data enrichment                | ⏳ Not started | Persisting cost basis deltas and unrealised gain/loss data still needs modelling and ETL updates.                                                                                    |
| Frontend analytics             | 🚧 In progress | Vue client can request scoped transactions; UI work for allocation visualisations and CSV export is still pending.                                                                   |
| Interaction polish             | 🚧 In progress | Backend filter plumbing is complete, but UI caching of filters and security detail drawer UX are open tasks.                                                                         |

## Backend priorities

1. **Reliability & coverage**
   - Expand unit/integration tests to validate webhook-triggered refreshes, deduplication, and error handling (start with fixtures in `tests/test_plaid_webhook.py`).
   - Instrument refresh counts, durations, and error totals; ensure log lines capture Plaid `item_id` and `account_id` context.
2. **Data enrichment**
   - Persist cost basis, unrealised gain/loss, and day change figures to feed analytics.
   - Consider background jobs for nightly price reconciliation if Plaid data is delayed.

## Frontend priorities

1. **Analytics views**
   - Build allocation visualisations by account/institution/security and surface simple performance snapshots.
   - Add CSV export for investment transactions with filter state encoded in the query.
2. **Interaction polish**
   - Implement a security detail drawer with quote metadata and recent activity.
   - Provide filters by security, type/subtype, and date range; cache last-used filters per user (API support shipped 2025-09-17, UI persistence still pending).

## Operational tooling

- Maintain optional backfill scripts for historical investment transactions when onboarding legacy institutions.
- Document manual recovery steps for webhook failures (e.g., replay via `/api/plaid/investments/refresh`).

## Definition of done

- ✅ Automated tests cover webhook-driven refreshes, manual refresh endpoints, and core upsert helpers.
- ✅ Dashboards present allocation/performance insights with export functionality.
- ✅ Metrics and runbooks exist for monitoring investment data freshness.

_Last updated: 2025-09-17_
