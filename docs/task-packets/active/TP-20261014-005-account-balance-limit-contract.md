# TP-20261014-005: Account balance, limit and freshness contract

**Packet ID:** TP-20261014-005  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261014-005-account-balance-limit-contract.md`  
**Workstream size:** One independently testable implementation packet  
**Depends on:** None  
**Priority:** High  
**Series:** Accounts audit 1 of 5  
**Audited paths:** Accounts frontend and backend on 2026-10-14; prior head d38bd3d  

## Objective
Account balance, limit and freshness contract. Implement against current main with no repository-wide rediscovery.

## Current state and exact implementation

**Current seams**
- `backend/app/models/account_models.py:Account`: has balance and apr; no limit, available, mask, or observed-balance timestamp.
- `backend/app/helpers/plaid_helpers.py:get_accounts`: uses `acct.balances.available or acct.balances.current`, conflating available/current and treating 0 as missing.
- `backend/app/sql/account_logic.py:upsert_accounts` and `refresh_data_for_plaid_account`: parse `balances.current or ...`, discarding valid zero and not persisting credit limit.
- `backend/app/routes/accounts.py:list_accounts`: omits mask, apr, limit, account_type, is_investment, and status expected by `frontend/src/views/Accounts.vue:linkedAccounts`.
- Two balance-normalization helpers exist: `backend/app/sql/account_logic.py:normalize_balance` and `backend/app/utils/finance_utils.py:normalize_account_balance`. Verify sign applied once, not twice.

**Implement**
1. `backend/app/models/account_models.py`: nullable columns `credit_limit`, `available_balance` Numeric(18,2); `mask` String(8); `currency_code` String(8); `balance_as_of` DateTime. Add one NEW Alembic revision under `backend/migrations/versions/` based on CURRENT head (check `flask db heads` in configured dev DB), plus matching `docs/backend/migrations/versions/<revision>.md`. No destructive migration/backfill assumptions.
2. `backend/app/sql/account_logic.py`: in both ingestion paths use explicit null handling: `balances=payload.get('balances') or {}; current=balances.get('current'); limit=balances.get('limit'); available=balances.get('available')`. Preserve valid zero and existing data when absent; no `or 0` for unknown values. Provider limit is credit-only; checking overdraft limit is NOT card credit line. Store currency/mask/observed timestamp. One canonical sign normalization. Never multiply loan balances with credit-card available balance.
3. `backend/app/helpers/plaid_helpers.py:get_accounts`: do not use available as observed current balance in `update_account_history`; no `available or current`.
4. `backend/app/routes/accounts.py:list_accounts`: additive nullable `credit_limit`, `limit` alias for credit, `available_balance`, `mask`, `currency_code`, `balance_as_of`, `apr`, `account_type`, `is_investment`, `status`. Keep connection-status and include_hidden behavior. Do not expose tokens or full account numbers.
5. New `backend/app/services/account_portfolio_metrics.py`: canonical groups depository, investment, credit, loan, other; owed = max(-signed_balance,0) for liabilities; card utilization = owed/credit_limit*100 when limit>0 else null; overlimit explicitly; provider available_credit prioritized, else call remaining *derived* headroom, not issuer available. Do not silently turn missing into 0.

**Tests** `tests/test_save_plaid_account.py`, `tests/test_account_display_name.py`, `tests/test_accounts_product_scopes.py`, new `tests/test_account_portfolio_metrics.py`: valid zero, missing current, missing limit, 0/negative credit balance, negative-credit refunds, sign idempotence, investment/loan, hidden/closed, missing freshness, serialized mask. Run `pytest -q tests/test_account_portfolio_metrics.py tests/test_save_plaid_account.py tests/test_accounts_product_scopes.py`, migration check against verified DB, `pre-commit run --all-files`.

**Non-goals** Paid real-time Plaid balance call, fake missing limits, UI redesign. **Accept:** fields survive connect/refresh/API; truthful nulls; no double liability sign; backward compatible.


## Implementation order and closeout
1. Check `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate named seams only.
2. Mark In Progress in packet and tracker. Complete changes in order listed; run focused tests then lint/build/available guards. For migrations verify dev DB target and live revision head first.
3. On pass mark Complete, move packet to completed/, update INDEX/TRACKER in same change, commit only packet-owned changes to origin/main with normal synchronization; never force push.
4. Report files changed, contracts, tests (honestly), screenshots if UI, deviations and exact blocker/resume condition.

## Do not rediscover
Avoid broad repo archaeology. Only inspect explicitly named paths, directly imported helpers/tests, and exact migrations/route registrations needed to implement this packet.
