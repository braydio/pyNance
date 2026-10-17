# TP-20261016-002: Recurring Stream Persistence, Account Scope and Legacy API Repair

**Packet ID:** TP-20261016-002  
**Status:** In Progress  
**Created:** 2026-10-16  
**Last updated:** 2026-10-16  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-002-recurring-schema-api-integrity.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P0  
**Depends on:** None  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Recurring Stream Persistence, Account Scope and Legacy API Repair. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `backend/app/models/transaction_models.py`
- `backend/app/models/__init__.py`
- `backend/migrations/versions/<new_revision>_recurring_streams.py (new unique Alembic revision)`
- `backend/app/services/recurring_repository.py (new)`
- `backend/app/routes/recurring.py`
- `backend/app/sql/recurring_logic.py`
- `tests/test_routes_recurring.py`
- `tests/test_recurring_repository.py (new)`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
`RecurringTransaction` ORM defines `transaction_id` NOT NULL FK, `account_id`, `frequency`, `next_due_date`, `notes` but no `description`/`amount`; `routes/recurring.py:update_recurring_tx` and its GET/DELETE query the missing columns and create a `RecurringTransaction` without mandatory `transaction_id`. UI requires a transaction ID for manual creation yet PUT payload omits it. `sql/recurring_logic.upsert_recurring` creates a fabricated Transaction when no real matching transaction exists. `scan_account_for_recurring` is account-scoped but doesn't prove ownership.

## Required code edits, in order
1. Create `RecurringStream` table/model as canonical user-confirmed recurring identity, WITHOUT requiring a transaction row: `id UUID/string(36) PK`, `user_id VARCHAR(64) NOT NULL`, `account_id VARCHAR(64) FK accounts.account_id NOT NULL`, `merchant_key VARCHAR(160) NULL`, `display_name VARCHAR(256) NOT NULL`, `amount_cash_delta NUMERIC(18,2) NOT NULL`, `amount_mode VARCHAR(16) NOT NULL CHECK fixed|variable`, `cadence VARCHAR(20) NOT NULL CHECK once|weekly|biweekly|semimonthly|monthly|quarterly|yearly`, `anchor_date DATE NOT NULL`, `status VARCHAR(16) NOT NULL CHECK proposed|confirmed|ignored|ended`, `source VARCHAR(16) NOT NULL CHECK manual|detected|legacy`, `confidence NUMERIC(4,3) NULL`, `last_observed DATE NULL`, `created_at/updated_at TIMESTAMPTZ NOT NULL`, optional `confirmed_at TIMESTAMPTZ`, `notes TEXT NULL`; indexes `(user_id,status,anchor_date)`, `(user_id,account_id,merchant_key)`; avoid false uniqueness on merchant because one merchant can have multiple plans.
2. Create `RecurringStreamEvidence`: `id BIGINT PK`, `stream_id FK recurring_streams.id ON DELETE CASCADE`, `transaction_id VARCHAR(64) NULL` (logical reference, not cascading FK, to survive source retirement), `observed_at DATE`, `raw_amount NUMERIC`, `canonical_amount NUMERIC`, `merchant_key`, `decision VARCHAR(24)`, `reason JSON`, `created_at`; UNIQUE `(stream_id,transaction_id)` where transaction_id non-null. Do not store credentials/raw access tokens; evidence immutable after ingest except explicit erasure. SQLite migration supports and Postgres checks; name down_revision after inspecting current Alembic head.
3. `recurring_repository.py`: `create_manual`, `update_stream`, `delete_or_end_stream`, `list_streams` by owner/account, validate account membership BEFORE writes, represent financial amounts as Decimal. User identity MUST be a trusted server-side principal; never trust arbitrary payload `user_id`. If deployment lacks authenticated principal, keep new mutation API gated or bind to explicitly configured single-tenant owner with server-only env and reject nonowner; no broadened open access.
4. `routes/recurring.py` legacy `PUT/DELETE /api/recurring/accounts/<account_id>/recurringTx` and `GET /api/recurring/<account_id>/recurring`: delegate to new repository for compatibility, infer description/amount only from an actual owner-scoped transaction if tx_id supplied, otherwise accept explicit manual fields. Reject ambiguous delete by description/amount with 409 and direct client to ID-based endpoint created in packet 005. GET `reminders` maintains compatibility and uses confirmed stream data; default 7-day view doesn't become a full inventory. Remove fabricated transaction in `sql/recurring_logic.upsert_recurring`; route old detector through packet 004 later. Preserve existing legacy `recurring_transactions` table and audit/migrate valid rows safely, skipping orphan/conflicting rows with counters (no destructive DROP).

## Exact contracts and acceptance fixtures
- A manual rule can exist with no transaction ID. A user may create `Duke Energy`, variable monthly, negative amount and anchor date, scoped to owned account. A foreign account returns 403/404 with no mutation.
- Legacy GET and PUT continue returning documented shapes; old `recurring_transactions` records are readable/migratable without loss or fake bank activity; secrets and foreign user's streams never exposed.

## Validation commands
`pytest tests/test_routes_recurring.py tests/test_recurring_repository.py tests/test_recurring_bridge.py -q`; Alembic upgrade/downgrade against dev Postgres and SQLite test environment; duplicate/idempotent/unauthorized/legacy cases.

## Non-goals
Do not add fictitious Transactions, break existing scan URL, silently delete legacy rows, or implement candidate detection/UI in this packet.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.
