# Transactions Sync Roadmap

## Snapshot

- `app/services/plaid_sync.py` manages Plaid delta-sync with paging, atomic apply, and cursor persistence.
- `/api/plaid/transactions/sync` triggers syncs on demand while `/api/webhooks/plaid` processes `TRANSACTIONS:SYNC_UPDATES_AVAILABLE` notifications.
- Raw Plaid payloads are archived in `plaid_transaction_meta.raw` for audit and replay.

## Current coverage

- Service behaviour and webhook wiring are exercised in `tests/test_plaid_webhook.py` (service stubs, webhook fan-out, and cursor updates).
- Legacy `transactions/get` helpers remain only for manual backfills and are isolated from default flows.

## Outstanding priorities

1. **Hardening & observability**
   - Add focused unit tests for `sync_account_transactions` covering removed transaction handling, duplicate cursor submissions, and error propagation.
   - Emit metrics for sync duration, added/modified/removed counts, and webhook failure rates. Wire alerts for sustained failures.
2. **Migration closure**
   - Track per-item migration state (historical vs. fast-forward) so support can verify onboarding decisions.
   - Remove remaining `transactions/get` references once all items carry a stored cursor and first sync has succeeded.
3. **Operational tooling**
   - Document backfill procedures and provide scripts for bounded historical imports when requested by users.

## Implementation guidance

- Keep sync idempotent: new tests should verify that reprocessing the same webhook payload leaves the database unchanged.
- Update the Plaid client configuration (`app/extensions.py`) if new scopes are required, and document the change in `docs/integrations/`.
- Ensure retry logic surfaces actionable errors—wrap Plaid exceptions with context that includes `item_id` and `account_id` without logging sensitive fields.

## Definition of done

- ✅ Every Plaid item has a stored `sync_cursor` and is migrated away from legacy fetches.
- ✅ Webhook and manual sync entry points are covered by automated tests (unit + integration) with deterministic fixtures.
- ✅ Metrics and runbook entries exist for sync monitoring, and on-call responders can replay failed syncs quickly.

_Last updated: 2025-09-10_
