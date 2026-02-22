# `plaid_sync.py`

## Responsibility

- Coordinate Plaid's `/transactions/sync` workflow for individual accounts, applying additions, modifications, and removals atomically.
- Keep Plaid-specific metadata (cursor, last refreshed timestamp, personal finance categories) synchronized with local transaction rows.

## Key Functions

- [`sync_account_transactions(account_id)`](../../../../backend/app/services/plaid_sync.py): Main entry point that resolves the Plaid access token, iterates through paginated sync batches, and persists cursor updates for every account under the Plaid item.
- Internal helpers:
  - [`_upsert_transaction(tx, account, plaid_acct)`](../../../../backend/app/services/plaid_sync.py): Applies transaction rules, maps Plaid categories to [`Category` models](../../../../backend/app/models.py), refreshes metadata via [`refresh_or_insert_plaid_metadata`](../../../../backend/app/sql/refresh_metadata.py), and detects internal transfers through [`detect_internal_transfer`](../../../../backend/app/sql/account_logic.py).
  - [`_apply_removed(removed)`](../../../../backend/app/services/plaid_sync.py): Deletes transactions that Plaid reports as removed to maintain parity with the external feed.

## Dependencies & Collaborators

- Plaid SDK: `TransactionsSyncRequest` request model (v13+ API surface).
- SQLAlchemy models: `Account`, `Transaction`, `PlaidAccount`, `Category`.
- SQL helpers: [`app/sql/account_logic.py`](../../../../backend/app/sql/account_logic.py) for transfer detection and category normalization; [`app/sql/transaction_rules_logic.py`](../../../../backend/app/sql/transaction_rules_logic.py) for user-specific rule application; [`app/sql/refresh_metadata.py`](../../../../backend/app/sql/refresh_metadata.py) for auxiliary Plaid metadata.
- Shared logging via [`app.config.logger`](../../../../backend/app/config.py) and Plaid client configuration in [`app.config.plaid_client`](../../../../backend/app/config.py).

## Usage Notes

- Sync cursors are persisted per Plaid item, so subsequent accounts linked to the same item reuse progress and benefit from incremental fetches.
- Database commits occur per batch to keep additions, modifications, and deletions consistent; failures trigger rollbacks and surface through logged errors.


## Merchant normalization

Both transaction ingestion paths use `app.utils.merchant_normalization.resolve_merchant` to enforce a shared fallback order (`merchant_name` -> `name` -> `description` -> `Unknown`). The helper strips common processor prefixes (for example `POS`, `SQ *`, and `PAYPAL *`), normalizes case/spacing, and emits a canonical `merchant_slug`. Ingestion preserves the raw source description in `Transaction.description` while persisting normalized merchant fields and metadata.
