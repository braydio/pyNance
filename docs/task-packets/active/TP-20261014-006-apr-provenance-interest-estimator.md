# TP-20261014-006: APR provenance and interest inference guardrails

**Packet ID:** TP-20261014-006  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261014-006-apr-provenance-interest-estimator.md`  
**Workstream size:** One independently testable implementation packet  
**Depends on:** TP-20261014-005  
**Priority:** High  
**Series:** Accounts audit 2 of 5  
**Audited paths:** Accounts frontend and backend on 2026-10-14; prior head d38bd3d  

## Objective
APR provenance and interest inference guardrails. Implement against current main with no repository-wide rediscovery.

## Current state and exact implementation

**Current seams**
- `backend/app/models/account_models.py:Account.apr` has no provenance.
- `backend/app/services/plaid_sync.py:_estimate_interest_apr` uses `charge/(current_balance-charge)*12*100`; `_update_account_apr_from_interest_charge` runs inside `_upsert_transaction` on each interest event, overwrites previous rate during replay.
- `tests/test_merchant_normalization.py:test_upsert_transaction_estimates_apr_from_interest_charges` asserts the flawed 24.4898% result and must be changed, not preserved.
- `backend/app/services/enhanced_account_history.py` produces reconstructed daily balances; not independently verified interest-bearing average daily balance.

**Implement**
1. Stop APR mutation in `backend/app/services/plaid_sync.py:_upsert_transaction` immediately. Keep transaction ingestion intact; never overwrite provider/manual APR with an estimated rate.
2. Add nullable Account metadata `apr_source` (provider, manual, estimated, legacy_unverified), `apr_as_of`, `apr_confidence`, `apr_sample_cycles`, `apr_details` JSON for multi-APR card buckets; new Alembic revision with CURRENT actual head and matching migration docs. Existing populated `apr` with unknown provenance is `legacy_unverified`, NOT provider. APR stored in percentage units (23.49, not .2349).
3. Add `backend/app/services/account_interest_rates.py`: classify POSTED, non-reversed interest charges by reliable transaction PFC/category + conservative exact description matching, with account/product scope; exclude interest credits, generic bank fees, pending, duplicated events and loans/portfolios without qualifying data. Return observed interest paid by exact period even without APR.
4. Estimate *only when* >=2 complete coherent statement cycles and a real interest-bearing ADB or independently observed complete daily balances. Formula: `100 * period_interest / verified_average_interest_bearing_balance * 365 / period_days`; account for mixed APR buckets, promos, changing balance, varying cycle lengths, large estimate dispersion and zero/unknown denominator. If not defensible, return APR estimate null, show observed interest charges instead. NEVER use reconstructed balance history as verified ADB, never call effective annualized charge rate a confirmed contractual APR. Only reported provider or explicit manual can claim that.
5. Add optional API fields `apr_source`, `apr_as_of`, `apr_details`, `estimated_rate`, `interest_paid_recent` via `backend/app/routes/accounts.py:list_accounts`, with coverage/source markers. Update `docs/backend/app/services/plaid_sync.md`, new service doc and migration doc.

**Tests** Replace flawed APR assertion in `tests/test_merchant_normalization.py`; create `tests/test_account_interest_rates.py` for pending/reversal, a single charge, duplicated sync, two verified 30-day ADB cycles, 0 denominator, transfers, promo/mixed rate, provider precedence, legacy unverified. `pytest -q tests/test_account_interest_rates.py tests/test_merchant_normalization.py tests/test_plaid_ingestion_integrity.py`.

**Non-goals** No claim that generic interest transaction can supply APR, no forecast or payment schedule. **Accept:** no replay overwrites rates; estimates clearly qualified/null when unknown; raw observed interest still useful.


## Implementation order and closeout
1. Check `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate named seams only.
2. Mark In Progress in packet and tracker. Complete changes in order listed; run focused tests then lint/build/available guards. For migrations verify dev DB target and live revision head first.
3. On pass mark Complete, move packet to completed/, update INDEX/TRACKER in same change, commit only packet-owned changes to origin/main with normal synchronization; never force push.
4. Report files changed, contracts, tests (honestly), screenshots if UI, deviations and exact blocker/resume condition.

## Do not rediscover
Avoid broad repo archaeology. Only inspect explicitly named paths, directly imported helpers/tests, and exact migrations/route registrations needed to implement this packet.
