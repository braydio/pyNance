# Transactions Sync Roadmap

## Snapshot

- `app/services/plaid_sync.py` manages Plaid delta-sync with paging, atomic apply, and cursor persistence.
- `/api/plaid/transactions/sync` (registered via `plaid_transactions` with `/api/plaid/transactions` prefix) triggers syncs on demand, while `/api/webhooks/plaid` (registered via `plaid_webhooks` with `/api/webhooks` prefix) processes `TRANSACTIONS:SYNC_UPDATES_AVAILABLE` and `TRANSACTIONS:DEFAULT_UPDATE` notifications.
- Raw Plaid payloads are archived in `plaid_transaction_meta.raw` for audit and replay.

## Current coverage

- Service behaviour and webhook wiring are exercised in `tests/test_plaid_webhook.py` (service stubs, webhook fan-out, and cursor updates).

## Migration status (route wiring)

Migration is still partial: transaction refresh traffic uses both the cursor-based sync path and legacy `/transactions/get` path.

### Cursor-driven endpoints (`/transactions/sync`)

- `POST /api/plaid/transactions/sync` directly calls `plaid_sync.sync_account_transactions`.
- `POST /api/webhooks/plaid` calls `plaid_sync.sync_account_transactions` for `TRANSACTIONS` webhooks (`SYNC_UPDATES_AVAILABLE`, `DEFAULT_UPDATE`).

### Legacy endpoints (`/transactions/get`)

- `POST /api/accounts/refresh_accounts` still routes transaction refreshes through `account_logic.refresh_data_for_plaid_account`.
- `POST /api/accounts/<account_id>/refresh` still routes transaction refreshes through `account_logic.refresh_data_for_plaid_account`.
- `POST /api/plaid/transactions/refresh_accounts` still routes through `account_logic.refresh_data_for_plaid_account`.
- `POST /api/institutions/<institution_id>/refresh` still routes through `account_logic.refresh_data_for_plaid_account`.

### Quick verification references

- Blueprint registration and URL prefixes: `backend/app/__init__.py`.
- Cursor endpoints: `backend/app/routes/plaid_transactions.py`, `backend/app/routes/plaid_webhook.py`.
- Legacy route handlers: `backend/app/routes/accounts.py`, `backend/app/routes/plaid_transactions.py`, `backend/app/routes/institutions.py`.
- Legacy helper implementation (`get_transactions` using `/transactions/get`): `backend/app/sql/account_logic.py`, `backend/app/helpers/plaid_helpers.py`.

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

_Last updated: 2026-03-13_
