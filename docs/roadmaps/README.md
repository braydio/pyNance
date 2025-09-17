# pyNance Roadmaps Overview

This directory consolidates the active product roadmaps for pyNance so they live alongside the wider developer documentation. Each workstream summary below links to a dedicated plan that tracks status, deliverables, and testing expectations.

## Workstream directory

| Area                   | Current focus                                                             | Detailed plan                                  |
| ---------------------- | ------------------------------------------------------------------------- | ---------------------------------------------- |
| Accounts experience    | Balance history visualisation, range filters, and richer account insights | [Accounts roadmap](./accounts.md)              |
| Transactions sync      | Plaid delta-sync hardening, webhook coverage, and migration clean-up      | [Transactions sync roadmap](./transactions.md) |
| Planning & allocations | Bill management UI, allocation enforcement, and Flask planning APIs       | [Planning roadmap](./planning.md)              |
| Investments            | Holdings/transaction refresh reliability and analytics surfacing          | [Investments roadmap](./investments.md)        |

Additional feature planning (forecasting, routing refactors, and UI audit items) remains indexed under [`docs/maintenance/open_processes_index.md`](../maintenance/open_processes_index.md).

## Cross-cutting priorities

1. **Reliability & observability**
   - Expand unit and integration coverage for webhook entry points and sync flows.
   - Instrument sync counters, failure logging, and cursor advancement so regressions are caught quickly.
2. **Dashboard enrichment**
   - Continue surfacing the enriched metadata already stored in raw payloads (merchant logos, payment channels, location context).
   - Highlight actionable insights—category drill-downs, allocation warnings, and investment snapshots—inside the primary dashboards.
3. **Scheduling & recovery**
   - Maintain tooling for daily refresh fallbacks and bounded historical backfills when onboarding new institutions.
   - Document operational checklists so on-call responders can recover failed syncs without diving into code first.

## Operational guardrails

- `/api/webhooks/plaid` must stay reachable from Plaid; update `BACKEND_PUBLIC_URL` whenever environments change.
- Apply new database migrations immediately after pulling backend changes so JSON payload columns and indices remain in sync.
- Keep roadmap docs versioned alongside the code: update the relevant plan whenever a milestone completes or scope shifts.

_Last updated: 2025-09-10_
