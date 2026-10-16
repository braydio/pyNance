# TP-20261016-004: Unify Recurrence Detector with Forecast Pattern Evidence

**Packet ID:** TP-20261016-004  
**Status:** Ready  
**Created:** 2026-10-16  
**Last updated:** 2026-10-16  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-004-recurring-pattern-detection-unified.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P1  
**Depends on:** TP-20261016-001, TP-20261016-002  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Unify Recurrence Detector with Forecast Pattern Evidence. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `backend/forecast/v2_sources.py`
- `backend/app/services/recurring_detection.py`
- `backend/app/services/recurring_bridge.py`
- `backend/app/services/recurring_repository.py`
- `backend/app/services/recurring_candidate_service.py (new)`
- `backend/app/services/forecast_v2_sources.py`
- `backend/app/sql/recurring_logic.py`
- `tests/test_recurring_detection.py (new)`
- `tests/test_recurring_bridge.py`
- `tests/test_forecast_v2_sources.py`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
Legacy `RecurringDetector` keys on exact 2dp amount + first 16 cleaned description chars, needs 3 occurrences; `RecurringBridge` maps cadence 30 days and writes via fake transaction path. `/scan/<account_id>` uses a 90-day window. Separately `forecast/v2_sources.py:_infer_streams`, `_detect_cadence`, `_cluster_amounts` use merchant/sign/amount tolerance over 120 days; these are currently disconnected. `_SUPPORTED_FREQUENCIES` only supports up to monthly, yet manual UI offers yearly.

## Required code edits, in order
1. Make `forecast/v2_sources.py:_infer_streams/_detect_cadence` the single pure source of recurrence candidates; move reusable public façade to `recurring_candidate_service.py:detect_candidate_streams(transactions,accounts,as_of,lookback_days=400)`; use canonical signed amount from 001 exactly ONCE at the adapter. NO parallel detector. Turn `RecurringDetector` and `RecurringBridge` into compatibility wrappers; legacy `/scan` must call canonical service and never write synthetic Transaction.
2. Extend cadence handling and `v2_core.CADENCES` / `expand_scheduled_events` to support `quarterly` and `yearly`, and distinguish semimonthly vs biweekly. For monthly day 29/30/31 clamp to valid last day; month starts/ends and 28-34 day gaps should match. Annual/quarterly patterns need 400-800+ day lookback if available; if not, return `insufficient_history`/proposed, not fabricated confidence. Allow variable bills up to configurable dispersion without merging unrelated subscriptions; merchant_slug fallback, account_id+sign grouping; return explanation signals and evidence.
3. `detect_candidate_streams` returns deterministic records `{candidate_key, user/account, merchant_key, label, signed_median, amount_min/max, amount_mode, cadence, expected_next_date, observations, confidence, reason_codes, evidence:[transaction_id,date,amount]}`. Candidate key SHA-256 of `(user,account,merchant,sign,cadence,amount_cluster_version)` stable across rescans and pending-to-posted; use version marker and deterministic clustering, do not use volatile cluster ordinal alone. Exclude pending, transfers, duplicate rows, non-cash/non-liability and no-owner; preserve user corrections.
4. Persist candidates via `recurring_repository.py:upsert_detected_candidate`; upsert by candidate_key with DB unique `(user_id,candidate_key)` added as nullable column if needed. NEVER overwrite `confirmed`, `ignored`, or `ended` with `proposed` on rescan; update latest evidence for proposed, preserve review decision. Candidate engine output used by Forecast V2 inference rather than its own second detector; explain and avoid double claiming.

## Exact contracts and acceptance fixtures
- Test $83/$97/$91 monthly utility across different month lengths; biweekly payroll; twice-monthly paychecks; annual subscription with 12+ months history; 3 different subscription tiers same merchant not merged; transfers and duplicate pending excluded.
- Scans are idempotent and no duplicated recurring streams; a previously rejected candidate stays rejected, confirmed unchanged.

## Validation commands
`pytest tests/test_recurring_detection.py tests/test_recurring_bridge.py tests/test_forecast_v2_sources.py tests/test_forecast_v2_core.py -q`; verify backtesting event counts and no double residual allocation. Use no extra Plaid API requests: detection runs solely on locally stored transactions.

## Non-goals
No LLM, Plaid Enrich calls, background scheduler or UI rewrites here. Don't automatically confirm lower-confidence patterns.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.
