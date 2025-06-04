## 📘 `sync_service.py`

```markdown
# Sync Service

## Purpose

Orchestrates synchronization jobs for pulling in external financial data from providers like Plaid, Teller, or CSV imports. Ensures consistent ingestion, deduplication, and transformation of external data sources.

## Key Responsibilities

- Poll external APIs for account, transaction, and balance data
- Trigger webhook-based or scheduled sync routines
- Normalize, validate, and store external financial records

## Primary Functions

- `run_sync(user_id, source="plaid|teller|csv")`

  - Main entrypoint to kick off sync routines by provider

- `ingest_transactions(transactions, source)`

  - Converts external transaction format to internal schema

- `deduplicate(entries)`
  - Filters out already-imported or stale entries

## Inputs

- External data from APIs or file uploads
- `user_id`, `account_id` contexts
- Timestamped sync anchors (last sync date, etc.)

## Outputs

- Imported records (accounts, transactions, balances)
- Log entries for sync history
- Alerts or warnings (e.g., missing auth, rate limits)

## Internal Dependencies

- `plaid_transaction_service`, `teller_transaction_service`
- `models.Transaction`, `models.Account`
- Background jobs scheduler, webhook responder

## Known Behaviors

- Performs deduplication across providers
- Logs detailed sync metadata for recovery/debugging
- Backfills are rate-limited to avoid API overuse

## Related Docs

- [`docs/dataflow/sync_jobs.md`](../../dataflow/sync_jobs.md)
- [`docs/models/SyncLog.md`](../../models/SyncLog.md)
```

---

Next: `transactions.py`?
