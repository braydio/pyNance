Project Roadmap (Q4)

Status Highlights

- Banking transactions use Plaid Transactions Sync with webhook automation and full raw payload capture.
- Investments refresh automatically via Plaid webhooks (transactions + holdings) with raw payload capture.
- Account history and net change endpoints power the Accounts dashboard.

Feature Priorities

1. Reliability & Observability
   - Add unit/integration tests for webhook paths (transactions + investments).
   - Add lightweight metrics/logging around sync counts, errors, and cursor advancement.

2. Dashboard Enrichment
   - Surface merchant logos, location, and payment channel in transaction details (using stored meta).
   - Category insights: drill‑downs using PFC data; improve icons and naming.

3. Investments Analytics
   - Allocation by account/institution/security with simple performance snapshots.
   - CSV export for investment transactions; filters by security/type/date.

4. Recurring Transactions
   - Improve detection heuristics and UX for editing/confirming rules.

5. Rule Engine Enhancements
   - More matchers (counterparty patterns, amount ranges, weekday rules), bulk re-apply, and rule hit metrics.

6. Scheduling & Backfill
   - Optional daily cron calling refresh endpoints as a fallback to webhooks.
   - Tooling for historical backfills (bounded date windows) when onboarding new items.

Operational Notes

- Webhook endpoint: `/api/webhooks/plaid` must be reachable by Plaid.
- Apply database migrations after pulling changes to ensure JSON columns exist.

Last updated: 2025-09-10
