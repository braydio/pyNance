# TP-20261017-006: Correct Safe-to-Spend Cash Basis and Remove Double Charges

**Packet ID:** TP-20261017-006  
**Status:** Ready  
**Created:** 2026-10-17  
**Last updated:** 2026-10-17  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261017-006-safe-spend-cash-basis-reconciliation.md`  
**Workstream size:** One cash-basis reconciliation packet  
**Priority:** P0  
**Depends on:** TP-20261016-001, TP-20261016-003, TP-20261016-007, TP-20261017-003  
**Series:** 005 payday; 006 cash basis; 007 horizon/UI; then existing 001/002 recurring projections.

## Objective
Ensure Safe-to-Spend starts with *real accessible liquid cash*, excludes deficit accounts and noncash activity, and never subtracts already-posted spending twice.

## Verified code seams (main 06c1ae48)
- `backend/app/services/safe_to_spend.py::_cash_account_payload` uses `normalize_account_balance(Account.balance,Account.type)` then `max(...,0)`. In `backend/app/utils/finance_utils.py::normalize_account_balance`, **non-liabilities use `abs(balance)`**; a -$100 overdraft becomes +$100 reported spendable cash.
- `Account.available_balance`, `Account.balance_as_of` exist in `backend/app/models/account_models.py` but are unused in Safe-to-Spend. `_is_cash_account` scans tokens in account **name** and type; risks false positives (name "cash back credit" etc).
- `_spent_between(as_of,as_of)` scans *all* visible account transactions, including credit-card charges and pending transactions, not just owned checking/savings; `build_safe_to_spend_payload` always subtracts this from current balances, double-debiting already-settled purchases.
- `_visible_accounts(None)` returns accounts across owners; `get_safe_to_spend` takes caller-provided `user_id`.

## Do not rediscover / exact edits
1. `backend/app/services/safe_to_spend.py::_is_cash_account`, `_cash_account_payload`: reuse typed classification from TP-20261016-007 for checking/savings/legitimate cash equivalent; no name-only inclusion. Exclude loans, credit cards, investments, brokerage shares, unverified cash-like naming, hidden and foreign accounts. Asset cash **must not** use the shared `abs()` normalization. `positive_cash_cents=max(0,min(current_balance,available_balance))` when both genuine current/available are reported; when availability missing use `max(0,current)` and explicit `availability_unverified` warning. Never use overdraft limits / credit limits as cash. `Account.balance_as_of` and source freshness included in `cash_coverage`; stale/missing data lowers confidence, not zero masquerading as verified. Preserve nonnegative integer cents, keep negative account balances as `deficit_cents` and deduct **total deficits across eligible cash accounts** from positive cash before clamping: checking -$100 and savings +$200 => at most $100 usable, not $200 or $300. Do not assume user can transfer every restricted fund; warn when availability uncertain.
2. `_spent_between` becomes posted **cash-outflow diagnostic** on same owner/scope, excluding internal transfers and card purchases. Exclude pending unless deliberately shown as a distinct pending component. Use canonical provider sign rules from TP-20261016-001. **Do not subtract posted outflows a second time from a current balance already incorporating them.** Keep `components.spent_today_cents` for history/visibility with `spent_today_included_in_balance=true|false|unknown`; default ambiguous balance-time treatment to unknown, not to an extra debit. For pending withdrawals use *only* reliable evidence they are not represented in available balance, otherwise show pending coverage rather than subtract twice.
3. `build_safe_to_spend_payload` changes only cash portion: `spendable_cash_cents` now after legitimate cash deficits; `opening_cash_sources` with sanitized balance/available/status age; `cash_coverage` counts missing/stale/uncertain; `current_balance_as_of` summary. `available`/bank snapshots not guaranteed to reflect the current second: no double counting of today activity. Ensure old legacy components keep names for API compatibility. No forecast model rewrite.
4. `backend/app/routes/dashboard.py`: route owner derived from trusted server principal (share with 005) and owner-scope enforced; do not accept an arbitrary request `user_id` as authority. Missing principal must not return all accounts; honor explicit supported single-user local dev mode only as existing server config permits.
5. `tests/test_safe_to_spend_service.py`, `tests/test_safe_to_spend_integration.py`, **new** `tests/test_safe_to_spend_cash_basis.py`: synthetic negative -100 and +200 => **<=100** consolidated cash; credit card spend today doesn't lower cash twice; posted checking -50 already in balance => no second deduction; pending transfer vs external cash debit; two-owner, stale availability, ambiguous overdraft; stable cent rounding and fixed `as_of`.

## Non-goals / validation
No provider refresh, bill projection, payday algorithms, account-balance DB schema changes or mutation, new paid APIs. Do not change global `normalize_account_balance` semantics in unrelated charts. `pytest tests/test_safe_to_spend_cash_basis.py tests/test_safe_to_spend_service.py tests/test_safe_to_spend_integration.py tests/test_transaction_semantics.py -q`. Update packet state INDEX/TRACKER on completion, report cash-basis fixture outputs and coverage cases.
