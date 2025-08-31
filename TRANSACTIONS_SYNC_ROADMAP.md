# 🚀 Roadmap: Plaid Transactions Sync Migration

## 1. Overview
Move pyNance from Plaid's legacy `transactions/get` flow to the delta-based `transactions/sync` API. The new model persists a per-item cursor and applies added/modified/removed transactions, eliminating redundant fetches and webhook complexity.

## 2. Current State
### Implemented
- **Data model** – `PlaidAccount` already has a `sync_cursor` column for storing per-item cursors.
- **Routing stub** – `POST /transactions/sync` endpoint exists and delegates to a service layer.
- **Legacy fetch** – Transaction ingestion uses Plaid's `transactions/get` with manual pagination.

### Missing
- **Provider sync logic** – `plaid.sync_transactions` and `teller.sync_transactions` implementations.
- **Cursor persistence** – logic to update `PlaidAccount.sync_cursor` after successful sync.
- **Webhook handler** – no listener for Plaid `SYNC_UPDATES_AVAILABLE` webhooks.
- **Patch application** – no atomic handling of added/modified/removed transactions.
- **Tests & monitoring** – no automated coverage for sync paths or webhook events.

## 3. Migration Plan
1. **Prerequisites**
   - Ensure Plaid SDK ≥9.4.0 is installed.

2. **Data Model**
   - Confirm `PlaidAccount.sync_cursor` is migrated and indexed.
   - Add `plaid_item_cursor` table if account-scoped cursors prove insufficient.

3. **Sync Service**
   - Implement `plaid.sync_transactions(access_token, cursor)` to call `/transactions/sync` with paging and mutation restart.
   - Apply added/modified/removed arrays in a single DB transaction, then persist the final `next_cursor` to `PlaidAccount.sync_cursor`.
   - Expose `sync_transactions(provider, account_id)` via existing service and route.

4. **Webhook Handler**
   - Add `/webhooks/plaid/transactions` endpoint responding to `SYNC_UPDATES_AVAILABLE` by invoking the sync service for the affected item.

5. **Onboarding Strategy**
   - For each existing item, choose: full historical sync (empty cursor) or fast-forward (`cursor="now"`).
   - Record migration choice in ops log.

6. **Cutover**
   - Feature flag items as they migrate.
   - Disable scheduled `transactions/get` jobs for migrated items.

7. **Decommission Legacy**
   - Remove `transactions/get` helper and related webhooks once all items use Sync.
   - Retain `/transactions/refresh` only for on-demand refresh UI.

## 4. Completion Metrics
- ✅ `plaid.sync_transactions` handles paging, mutations, and stores `next_cursor`.
- ✅ Webhook endpoint processes `SYNC_UPDATES_AVAILABLE` and triggers sync.
- ✅ Tests cover sync flow, webhook handler, and cursor persistence.
- ✅ Legacy `transactions/get` paths removed and all items have recorded cursors.

---
*Last updated: $(date -u +"%Y-%m-%d")*
