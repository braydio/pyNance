# Plaid source history and reconciliation

Owner: Backend
Last Updated: 2026-09-30
Status: Implemented

`backend/app/services/plaid_audit.py` writes immutable `plaid_source_events` alongside active transaction changes. The table deliberately has no foreign key to active transactions or linked accounts, so removal and unlinking cannot erase source history. PostgreSQL triggers reject updates, deletes, and truncation. Credentials are removed recursively before storage.

Each event has an original JSON payload and SHA-256 digest, transaction/account/item IDs, UTC observation time, endpoint, run ID, page index, event type, and available Plaid request ID and sync cursors. A unique `(run_id, page_index, event_type, transaction_id)` constraint makes retries within a run safe. Later runs retain later observations, even when the payload is unchanged. Provider observations and local retirement/correction snapshots use different event types. Local snapshots also retain annotations when a transaction is retired.

Both legacy `/transactions/get` and `/transactions/sync` call the shared `_upsert_transaction` projection. The provider payload is copied before transaction rules and merchant normalization, and latest metadata now contains that original copy. Rules affect the local projection rather than rewriting evidence. Older `raw` values may already contain rule changes; reconciliation labels their preserved snapshots `baseline` and cannot recover overwritten provider history.

## Integrity behavior

- PostgreSQL owner locks serialize a user's provider writes and transfer matching; item locks serialize sync checkpoints; transaction identity locks prevent query/insert races. Inserts also use database conflict handling. Category creation uses a global transaction lock to avoid opposite insertion order deadlocks during multi-category imports. Locks release on commit or rollback.
- Category identity is the canonical slug. Legacy primary/detailed category paths are provenance and can occur on multiple PFC categories. Ingestion never mutates a different canonical category to reuse its legacy path.
- User-modified fields are preserved, including complete category and merchant field groups. Legacy edit flags without a usable field list preserve all editable core fields. Rule category labels resolve consistently and create a canonical label when no category exists.
- Transaction/account/owner conflicts and invalid dates or amounts fail the batch. Missing provider dates never become today's date. Unknown sync accounts never fall back to the initiating account.
- A posted transaction's `pending_transaction_id` retires its pending predecessor, preserving source and annotations. Old pending observations cannot resurrect a predecessor when its posted successor is already stored. Same-amount/date/name purchases are not automatically merged.
- Retirement clears reciprocal transfer links, migrates tags and recurring references to a successor when applicable, and retains a tombstone independently of cascade deletion.
- Automatic transfers require opposite nonzero amounts, accounts owned by the same user, and evidence on both sides, within four calendar days. Pending transactions, payroll categories, unrelated purchases/refunds, and generic brokerage position activity are excluded. Equal-ranking matches must be unique in both directions. Explicit user decisions are preserved. Credit card payments emit `credit_card_payment`.
- Sync fetches all pages before applying changes. Pagination mutation restarts at the original cursor, up to three attempts. All source events, additions/modifications/removals, and sibling-account cursors commit together. Failures roll back the entire run.

## Reconciliation command

`scripts/reconcile_plaid_data.py` loads backend database configuration and never contacts Plaid. It defaults to a rollback-only rehearsal and writes a private JSON change report. It takes owner/category and table locks, snapshots every retained transaction into audit history, repairs ownership/date/category/merchant inconsistencies, retires explicitly linked pending predecessors, and rebuilds automatic transfer links. It validates ownership, pending replacements, duplicate IDs, and pair references before commit.

```bash
python scripts/reconcile_plaid_data.py --report /private/path/rehearsal.json
python scripts/reconcile_plaid_data.py --apply --report /private/path/applied.json
```

Apply the Alembic migration first (`flask db upgrade`); `--migrate --apply` can also apply this exact revision when the database is at its immediate predecessor. Back up the database with `pg_dump -Fc` and rehearse against an isolated restore before committing live corrections. `PYNANCE_RECONCILE_DATABASE_URI` selects an isolated restore without editing backend credentials. Protect reports and backups because they contain financial data. The correction report includes before/after values and an audit run ID; use the database audit events to identify removed predecessors. Restore the backup for a complete rollback; downgrading the audit migration deliberately refuses to erase evidence or merge newly distinct categories.

Unmatched stale pending rows and ambiguous transfers remain active for review. Merchant fallback is a normalized description when no merchant is provided; it is not independent proof of merchant identity. No correction claims to override a bank statement or reconstruct source snapshots that were never retained.

## Verification

`tests/test_plaid_ingestion_integrity.py` exercises source preservation, replay, pending retirement, user edits, ownership validation, invalid fields, category identity, removals, transfer ambiguity, legacy parity, and whole-run rollback. Cursor and merchant tests cover the updated persistence contract. PostgreSQL tests in `tests/test_plaid_ingestion_postgres.py` apply the real migration in a temporary schema and verify concurrent writes and immutable audit triggers; set `PYNANCE_TEST_DATABASE_URI` to an isolated PostgreSQL instance to run them.
