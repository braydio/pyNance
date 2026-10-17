# TP-20261017-005: Payday Detection with Sources, Confidence and Read-only Evidence

**Packet ID:** TP-20261017-005  
**Status:** Ready  
**Created:** 2026-10-17  
**Last updated:** 2026-10-17  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261017-005-payday-inference-evidence.md`  
**Workstream size:** One payday-inference/evidence implementation packet  
**Priority:** P0  
**Depends on:** TP-20261016-001, TP-20261016-002, TP-20261016-004, TP-20261016-005, TP-20261017-003  
**Series:** Safe-to-Spend reliability follow-up: 005 (payday), 006 (cash), 007 (display/horizons), then existing TP-20261017-001/002. Assume upstream packets land.

## Objective
Replace unverified cross-source deposit interval averaging with reproducible next-paycheck inference from locally stored, **posted cash income**, and a privacy-conscious diagnostic endpoint. Never label an unverified payday as confirmed or treat transfer-in as wages.

## Verified bug (main 06c1ae48)
`backend/app/services/safe_to_spend.py::_next_income_date(as_of,user_id)` fetches 90d of **all visible account** credits, ignores `Transaction.pending` and `is_internal`, keyword-matches category/description, mixes *all* income dates, averages every eligible 1..45-day gap, then predicts from last event. Two unrelated incoming deposits suffice. `get_safe_to_spend` exposes only `next_income_date`, no evidence. Existing `RecurringTransaction` and new stream review have no link to this function.

## Do not rediscover (exact implementation)
1. `backend/app/services/payday_inference.py` **(new)**: pure `infer_payday(posted_events, as_of, confirmed_streams=(), user_schedule=None)` returns
   `{next_payday,confidence,source,source_label,amount_cents|None,cadence,observed_dates,observed_amount_cents,history_start,history_end,reason_codes,needs_review}`.
   Precedence: user-confirmed schedule / confirmed owned income stream > inferred payroll-like stream with 3+ posted distinct cycles > unresolved. Group per stable employer/payer/account/stream, NOT all incomes together. Reuse canonical stream persistence & 004 evidence; never implement a second recurring detector. Prefer actual calendar semi-monthly anchors, biweekly 14d, weekly 7d, monthly day with month-end clamp; tolerate +/-3d posting/holidays with explicit confidence. Use fixed injected `as_of`, Decimal cents; no expected payday from just 2 unmatched credits or average of unrelated payer deposits. For multiple legitimate payers return separate candidates and deterministic nearest *eligible* predicted payday; never sum arbitrary payers into one cadence.
2. `backend/app/services/safe_to_spend.py::_next_income_date`: thin adapter to the detector for legacy callers; **do not return a claimed date** when evidence doesn't meet threshold. Candidate input: locally persisted last 180-400d of posted, visible, owner-confirmed cash account inflows, exclude internal/self transfers, brokerage movements, refunds, reversals, credit-card payments, pending. Reuse `transaction_semantics.canonical_account_delta` + `transaction_flow_classification.classify_reporting_flow` (001/003), `RecurringStream` repository (002/004/005); don't use raw income keyword scan as classifier. Missing history must yield `unknown/insufficient_history`, not a fake 14d payday. Do not count future expected income as current cash.
3. `backend/app/routes/dashboard.py::get_safe_to_spend` and **new** `GET /api/dashboard/payday-evidence?as_of=YYYY-MM-DD`: owner-scoped via validated session principal; never use user-supplied `user_id` to choose another account. If local development explicitly lacks auth, require existing supported single-user dev context or fail closed, don't invent an unauthenticated escape. Return structured evidence **only for request owner**, including redacted payer label, ISO dates, signed positive receipt amounts, cadence, next predicted date, confidence, reason codes, completeness and count; no bank tokens, raw memo, transaction ID, full account IDs, or third-party data. No paid Plaid refresh; GET is read-only. `/safe-to-spend` preserves `next_income_date` and adds `payday_prediction` metadata. Surface explicit "no validated payday" when none.
4. `tests/test_payday_inference.py` **(new)**; `tests/test_safe_to_spend_integration.py`; `tests/test_safe_to_spend_service.py` test route owner isolation, pending/transfer/payer grouping, partial history, biweekly skipped cycle, semimonthly 15th/EOM and leap Feb, monthly 31st, weekly, two vs three cycles, different employers, repeated paychecks on same date, user-confirmed override, stale sync and zero future-income credit. Ensure deterministic JSON with synthetic dates; no user financial fixture.

## Acceptance
With synthetic payroll on Sep 4, Sep 18, Oct 2, Oct 16, as_of Oct 17 => next Oct 30, `cadence=biweekly` with source evidence. Three unrelated inflows cannot imply Oct 30. Unconfirmed/ambiguous transfer cannot be a payday. If insufficient data, return `next_income_date=null` and explanation, **not** an invented date. No data from another owner.

## Tests / handoff
`pytest tests/test_payday_inference.py tests/test_safe_to_spend_service.py tests/test_safe_to_spend_integration.py -q`; verify read-only endpoint with development auth fixture. No migration, bank mutations, new provider calls, or unrelated forecast rewrite. Read AGENTS and packet index/tracker; set In Progress then Complete/move to completed and update index+tracker on validated commit. Report qualifying receipts and confidence for synthetic fixtures.
