# Investments Roadmap

## Snapshot

- Holdings, securities, and investment transactions are modelled via SQLAlchemy and refreshed through `upsert_investments_from_plaid` / `upsert_investment_transactions`.
- `/api/plaid/investments/refresh` (single item) and `/api/plaid/investments/refresh_all` (broadcast) trigger refreshes; `/api/investments` exposes read endpoints consumed by the Vue client.
- Plaid webhooks for `INVESTMENTS_TRANSACTIONS` and `HOLDINGS` are routed through `/api/webhooks/plaid`, enabling automatic updates.

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
   - Provide filters by security, type/subtype, and date range; cache last-used filters per user.

## Operational tooling

- Maintain optional backfill scripts for historical investment transactions when onboarding legacy institutions.
- Document manual recovery steps for webhook failures (e.g., replay via `/api/plaid/investments/refresh`).

## Definition of done

- ✅ Automated tests cover webhook-driven refreshes, manual refresh endpoints, and core upsert helpers.
- ✅ Dashboards present allocation/performance insights with export functionality.
- ✅ Metrics and runbooks exist for monitoring investment data freshness.

_Last updated: 2025-09-10_
