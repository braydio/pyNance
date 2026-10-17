# TP-20261017-001: Project Recurring Cash Obligations into Safe-to-Spend

**Packet ID:** TP-20261017-001  
**Status:** Ready  
**Created:** 2026-10-17  
**Last updated:** 2026-10-17  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261017-001-recurring-safe-to-spend-obligation-projection.md`  
**Workstream size:** One backend integration packet  
**Priority:** P0  
**Depends on:** TP-20261016-001, TP-20261016-002, TP-20261016-004, TP-20261016-005, TP-20261017-006, TP-20261017-007  
**Series:** 2 follow-on packets: TP-20261017-001 then -002. Existing 20261016 packets remain authoritative for detection/storage/review; assume dependencies have landed.  

## Objective
A recognized recurring external cash debit due within the **protection horizon** (TP-20261017-007), even beyond today's one-day display window, must reserve cash exactly once, even when no `PlannedBill` was manually created. Preserve the distinction between user-confirmed and high-confidence *provisional* obligations. This is a synthetic regression, not a user/account fixture.

## Do not rediscover: exact ownership
- `backend/app/services/safe_to_spend.py`: `_upcoming_bill_payload`, `build_safe_to_spend_payload`, `_horizon_end`, `_cash_account_payload`, `_spent_between`.
- `backend/app/services/recurring_obligation_projection.py` **(new)**: pure/deterministic `project_cash_obligations`.
- `backend/app/services/recurring_repository.py` (from 002/004): owner-scoped confirmed streams + durable candidates.
- `backend/forecast/v2_core.py`: reuse `expand_scheduled_events` calendar anchoring; do not write another monthly date calculator.
- `backend/app/models/planning_models.py`: `PlannedBill`, `PlanningScenario` (read only).
- `backend/app/routes/dashboard.py`: `get_safe_to_spend` only for trusted owner scoping / backward-compatible response.
- `tests/test_safe_to_spend_service.py`, `tests/test_safe_to_spend_integration.py`, `tests/test_recurring_obligation_projection.py` **(new)**.

## Verified code seam (main 65433b2315bd44904079a2b090ccf6502a96ddd0)
`safe_to_spend._upcoming_bill_payload` exclusively queries `PlannedBill.query.join(PlanningScenario)`; `build_safe_to_spend_payload` subtracts that result. Neither reads `RecurringTransaction`, new `RecurringStream`, nor Forecast V2 candidates. `_horizon_end` is today / today+6d / next payday (else today+14d). Existing `PlannedBill` rows belong to scenarios; summing every scenario may double count what-if bills. Existing `_spent_between` may also double-subtract posted activity already reflected in current account balance, requiring a balance-basis check.

## Implementation order and contracts
1. **Normalize eligible cash debits.** Load only owner-verified visible *cash-like* accounts, using the trusted server principal established by 002; never rely on caller-supplied `user_id` to widen scope. Reuse `recurring_repository` read methods for `confirmed` manual/detected streams and `proposed` candidate evidence, including `ignored/ended` suppression. Reuse sign conversion from 001 once. Do **not** treat a card purchase as an immediate checking debit; do include a scheduled payment *leaving checking/savings for an outside lender*, even if category says debt/transfer. Suppress confirmed paired **own-account** transfers. Skip missing account ownership or ambiguous sign with coverage reason, never invent an amount.
2. **Expand dates at read time**, not by inserting `PlannedBill` rows. Use `forecast.v2_core.expand_scheduled_events` to enumerate every occurrence within inclusive `[as_of,protection_horizon_end]`, correctly clamping Jan 31 -> Feb end and supporting biweekly/semimonthly/quarterly/yearly. For fixed amounts use persisted Decimal cents. For variable use explicit user amount when present, else documented deterministic conservative estimate based on eligible posted evidence (e.g. recent non-outlier upper quartile); expose estimate/range and do not overstate certainty. A future bill MUST NOT be described as due *today*, but it MUST reduce the safety-protected total if due before the next paycheck/14-day fallback (TP-20261017-007).
3. **Reserve confirmed + qualifying high-confidence provisional obligations.** Confirmed streams count once. A candidate can reserve provisionally only if the canonical 004 detector has at least 3 distinct posted cycles, well-aligned calendar phase, confidence >=0.85, an external cash debit, and no user rejection/override. This is a *temporary safety reserve*, NOT a change of candidate status to `confirmed`; label and allow rejection via 005. Two-transaction proposals are visible as `needs_review` but do not silently debit Safe-to-Spend. Candidate freshness/partial-history problems lower confidence; do not call a paid Plaid API. Define `confirmed_cents`, `provisional_cents`, `needs_review_cents` separately.
4. **Deduplicate before summing.** Merge eligible active-baseline `PlannedBill` occurrences with recurring projections. Prefer explicit user-entered PlannedBill > confirmed stream > provisional, but only suppress duplicates when same owner/account, billing cycle, and explicit shared source id or a unique unambiguous merchant+date(+/-3d)+amount match; keep distinct same-merchant subscription tiers. Do not sum alternate PlanningScenario what-if variants. Stable key: `(owner,account,source_stream_or_bill_id,occurrence_date)`. A recurring source ID must not be counted as both planned and recurring. Preserve manual one-off bills.
5. **Return auditable API math.** In `build_safe_to_spend_payload`, substitute `_upcoming_bill_payload` with the merged projection (compat wrapper is fine). Preserve existing keys and set `components.upcoming_outflows_cents = planned_cents + confirmed_recurring_cents + provisional_recurring_cents`; add three component splits, `needs_review_cents` informational only, and `upcoming_bills[]` rows `{id,name,account_id,due_date,amount_cents,source,status,estimated,reason_codes}`. Add `obligation_coverage` warnings for no transactions/backfill/unknown phase; do not report `confidence=ready` merely because there is no PlannedBill. Use TP-20261017-006 cash-basis contract; never subtract `_spent_between` posted transactions already represented in the starting balance. Return display-window due vs protection-window reserved splits. No raw transaction IDs/tokens in dashboard JSON.
6. **Refresh behavior.** Recompute server-side on each Safe-to-Spend request using locally persisted canonical stream decisions; confirm/ignore/edit in 005 must affect the next response. No new scheduler, live vendor calls, or parallel recurring database. Use fixed injected `as_of` in tests.

## Exact regression fixtures
- Fixed synthetic monthly checking debit of **$700** on Jul 21 / Aug 21 / Sep 21, projected Oct 21: with `as_of=2026-10-17`, `mode=week` reserve **70,000 cents** exactly once; `mode=today` reports zero **due today** for Oct 21, but *reserves* $700 under the protection-horizon policy when the next payday is after Oct 21 (or the fallback reaches Oct 21); packet 002 labels it as a future protected obligation. Confirmed counts; 3-cycle >=0.85 provisional counts with `status=provisional`; ignored/ended never counts.
- Manual `PlannedBill` for same occurrence supersedes corresponding stream, totaling $700, never $1,400; separate valid second plan at same merchant remains included.
- Month-end Jan 31 -> Feb 28/29; 2-cycle candidate review only; variable 670/700/730; recurring amount with a missing historic payment and insufficient coverage; paid posted item no longer projected again for current period; checking-to-own-savings transfer excluded, checking-to-external-debt payment included, card purchase excluded.
- Two users, hidden/foreign accounts, alternative PlanningScenario, partial history, and stale evidence cannot leak/cause silent overconfidence.
- Existing legacy today/week/until_payday response fields stay intact; no live network.

## Focused validation
`pytest tests/test_safe_to_spend_service.py tests/test_safe_to_spend_integration.py tests/test_recurring_obligation_projection.py tests/test_recurring_detection.py tests/test_forecast_v2_core.py -q`; inspect as-of cash reconciliation and request payload with synthetic seed. If dependencies are not yet implemented, leave Ready/Blocked with exact dependency rather than building duplicate stream models.

## Non-goals
No new recurrence detector, no fake bank `Transaction` rows, no Plaid Enrich, no visual redesign, no automatic permanent confirmation of candidates, and no ledger-wide forecast rewrite.

## Completion / agent handoff
Read `AGENTS.md`, task-packets README/INDEX/TRACKER; validate only named symbols. Mark In Progress before implementation, run focused tests, publish on main without force, mark Complete/move to completed/update INDEX+TRACKER in one change. Report exact files, test results, component math for $700 fixture, and any unverified runtime import coverage. Next: TP-20261017-002.
