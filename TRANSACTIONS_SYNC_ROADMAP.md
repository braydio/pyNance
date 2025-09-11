# 🚀 Roadmap: Plaid Transactions Sync Migration

## 1. Overview

Move pyNance from Plaid's legacy `transactions/get` flow to the delta-based `transactions/sync` API. The new model persists a per-item cursor and applies added/modified/removed transactions, eliminating redundant fetches and webhook complexity.

## 2. Current State

### Implemented

- Data model – `PlaidAccount.sync_cursor` present and used to persist cursors.
- Plaid sync service – `app/services/plaid_sync.py` implements `/transactions/sync` with paging and atomic upserts/deletes; persists `next_cursor` and updates `last_refreshed`.
- Flask endpoint – `POST /api/plaid/transactions/sync` accepts `{ account_id }` and invokes the sync service.
- Legacy fetch – Still available via `refresh_accounts` for ad‑hoc range pulls during migration.

### Recently Completed

- Plaid webhooks – `/api/webhooks/plaid` handles `TRANSACTIONS:SYNC_UPDATES_AVAILABLE` and triggers account syncs.
- Raw payload storage – full Plaid transaction payload now stored in `plaid_transaction_meta.raw`.

### Remaining

- Tests & monitoring – unit tests for sync flow and webhook handler; add lightweight metrics/logging.

## 3. Migration Plan

1. **Prerequisites**
   - Ensure Plaid SDK ≥9.4.0 is installed.

2. **Data Model**
   - Confirm `PlaidAccount.sync_cursor` is migrated and indexed.
   - Add `plaid_item_cursor` table if account-scoped cursors prove insufficient.

3. **Sync Service**
   - Implemented in `app/services/plaid_sync.py` (paging, atomic apply, cursor persistence).
   - Exposed via `POST /api/plaid/transactions/sync`.

4. **Webhook Handler**
   - DONE: `/api/webhooks/plaid` handles transaction sync notifications and dispatches cursored sync per account.

5. **Onboarding Strategy**
   - For each existing item, choose: full historical sync (empty cursor) or fast-forward (`cursor="now"`).
   - Record migration choice in ops log.

6. **Cutover**
   - Feature flag items as they migrate (cursor presence can be the flag).
   - Disable scheduled `transactions/get` jobs for items once cursor is set and first sync completes.

7. **Decommission Legacy**
   - Remove `transactions/get` helper usage once all items use Sync. Keep `/accounts/refresh` for on-demand flows.

## 4. Completion Metrics

- ✅ `plaid.sync_transactions` handles paging, mutations, and stores `next_cursor`.
- ✅ Webhook endpoint processes `SYNC_UPDATES_AVAILABLE` and triggers sync.
- ✅ Tests cover sync flow, webhook handler, and cursor persistence.
- ✅ Legacy `transactions/get` paths removed and all items have recorded cursors.

---

_Last updated: 2025-09-10_
