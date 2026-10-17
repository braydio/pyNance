# TP-20261017-005: Payday Detection with Sources, Confidence and Read-only Evidence

**Packet ID:** TP-20261017-005  
**Status:** Complete  
**Created:** 2026-10-17  
**Last updated:** 2026-10-17  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261017-005-payday-inference-evidence.md`  
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

## Completion report (2026-10-17)

- **Detector** `backend/app/services/payday_inference.py` (new, pure): `infer_payday(posted_events, as_of, confirmed_streams=(), user_schedule=None, *, data_through=None)` returns `{next_payday, confidence, source, source_label, amount_cents, cadence, observed_dates, observed_amount_cents, history_start, history_end, reason_codes, needs_review, candidates}`. Events are grouped per payer; distinct pay dates (same-day duplicates collapse) need `MIN_CYCLES = 3`. Cadences: weekly, biweekly (with a `skipped_cycle` allowance), semimonthly (needs 4 dates because 3 alternating dates are ambiguous with drifting biweekly, so it returns `ambiguous_cadence`), monthly with month-end clamp. History older than two periods yields no date. Precedence: user schedule > confirmed income stream > inferred; inferred is always `needs_review` and never "confirmed".
- **Adapter** `safe_to_spend._next_income_date` now calls `_payday_prediction`, which reads only the configured owner's data via `load_classified_flows` (so `canonical_account_delta`, pending/hidden/internal exclusion and the shared flow classifier apply): classified `income` on depository accounts, minus interest/dividend/tax-refund/retirement. Confirmed `RecurringStream` income streams are passed in. The keyword scan (`_looks_like_income`) is gone. No claimed date when evidence is thin: `next_income_date` is `null` with reason codes.
- **API:** `/api/dashboard/safe-to-spend` keeps `next_income_date` and adds `payday_prediction` (candidates omitted). New read-only `GET /api/dashboard/payday-evidence?as_of=` returns the prediction with `validated`, `receipt_count`, dates, positive amounts, cadence, one-word payer label and reason codes only (no memo, transaction or account ids). Owner comes from `PYNANCE_OWNER_USER_ID`; unset => 503 `owner_not_configured`; a differing `user_id` => 403.
- **Tests (synthetic):** `tests/test_payday_inference.py` (17) plus new integration cases in `tests/test_safe_to_spend_integration.py` (route owner isolation and redaction, fail-closed, pending/internal/other-owner credits, payload metadata, confirmed stream). The old integration assertion that two keyword credits imply a payday was inverted. `pytest tests/test_payday_inference.py tests/test_safe_to_spend_service.py tests/test_safe_to_spend_integration.py -q` => 27 passed. Recurring, flow-classification and debt-settlement suites still pass.
- **Acceptance:** synthetic payroll Sep 4/18, Oct 2/16 with `as_of` Oct 17 => `2026-10-30`, `biweekly`, medium confidence. Two cycles or unrelated payers => `null`.
- **Real-data check (read-only):** the owner's history gives a biweekly payer with 28 cycles, last posted 2026-10-15, next `2026-10-29` (low confidence because past amounts vary by more than 30%, so no amount is claimed).
- **Not changed:** no migration, no provider calls, no forecast changes. Without `PYNANCE_OWNER_USER_ID` the Safe-to-Spend payday is now `null` (restart Flask after setting it).
