# TP-20261016-004: Unify Recurrence Detector with Forecast Pattern Evidence

**Packet ID:** TP-20261016-004  
**Status:** Complete  
**Created:** 2026-10-16  
**Last updated:** 2026-10-17
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261016-004-recurring-pattern-detection-unified.md`  
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

## 2026-10-17 evidence refresh: real scan payload loses identity (must fix in THIS packet)
`backend/app/routes/recurring.py::scan_account_for_recurring` currently passes only `amount`, `description`, `date` to `RecurringBridge(txs)`, **omitting `account_id`, `transaction_id`, `pending`, `provider`, `is_internal`**. The bridge tries to recover `account_id` from those dictionaries and therefore can pass `None` to the old `upsert_recurring`. The route converts amount for display before detection, while the Forecast V2 adapter currently forwards raw Plaid amounts (001 repairs that mismatch). The seven-day GET reminders route separately groups exact description/amount and never constitutes the candidate inventory.

**Mandatory additions to step 1 and tests:**
- Change `scan_account_for_recurring` to an owner-checked adapter into `detect_candidate_streams` with *transaction_id, account_id, date, raw_amount, provider, merchant_name, description, pending, is_internal, transfer linkage* preserved; normalize sign only once using 001. Never use `display_transaction_amount` for inference, and never invent a bank transaction when persisting candidates.
- Reuse `load_v2_source_data` / existing synced local Transaction history, not the route's fixed 90-day slice; request up to 400 days by default (800+ if configured/available for yearly), with an explicit `history_incomplete` outcome. Expose an idempotent **manual rescan** for already imported accounts through 005; schedule no new background jobs. Trigger re-evaluation on existing *successful* transaction-sync completion only if the current pipeline offers a safe idempotent hook; otherwise document that manual scan is required (do not claim automatic recomputation).
- Compare consecutive **calendar months** rather than exact 30-day gaps; annual/missing-cycle behavior as above. For just two aligned, non-duplicate posted cycles, preserve candidate evidence with reason `needs_review_insufficient_cycles`, not a fake confirmed bill. For >=3 consistent cycles and sufficient scope, expose robust confidence/last-seen info for provisional reserve policy in TP-20261017-001. Do not claim that proposed streams were automatically confirmed.
- Add route regression for 3 synthetic $700 debits on Jul/Aug/Sep 21 under one account (not a user data fixture): a repeated scan yields one stable, owner-scoped monthly candidate with next due Oct 21, canonical external cash direction, transaction IDs and evidence count; 2 occurrences remain review-only, changed bank memo doesn't split it, ignored candidate stays ignored, no fabricated Transactions.

**Downstream dependency:** TP-20261017-001 consumes these canonical, persisted candidates in Safe-to-Spend; TP-20261017-002 explains their inclusion / omission in the dashboard. Those packets do not own detection.

## Exact contracts and acceptance fixtures
- Test $83/$97/$91 monthly utility across different month lengths; biweekly payroll; twice-monthly paychecks; annual subscription with 12+ months history; 3 different subscription tiers same merchant not merged; transfers and duplicate pending excluded.
- Scans are idempotent and no duplicated recurring streams; a previously rejected candidate stays rejected, confirmed unchanged.

## Validation commands
`pytest tests/test_recurring_detection.py tests/test_recurring_bridge.py tests/test_forecast_v2_sources.py tests/test_forecast_v2_core.py -q`; verify backtesting event counts and no double residual allocation. Use no extra Plaid API requests: detection runs solely on locally stored transactions.

## Non-goals
No LLM, Plaid Enrich calls, background scheduler or UI rewrites here. Don't automatically confirm lower-confidence patterns.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.

## Completion report (2026-10-17)

- Single detector: `forecast/v2_sources.py` (`_infer_streams`, `_detect_cadence`, `_cluster_amounts`) is the only recurrence engine. New pure `infer_candidate_streams(...)` exposes it; `build_v2_inputs` uses the same functions and now infers over `stream_lookback_days` (default 400) while allocation, reconciliation and the residual model keep `lookback_days` (120).
- Cadence: calendar-month comparison for monthly (month gap 1, 24-38 days), new `quarterly` and `yearly` in `v2_core.CADENCES` / `_occurrence_dates` (month-end clamped), `_SUPPORTED_FREQUENCIES` and lapse windows; semimonthly vs biweekly kept distinct. Variable bills chain-cluster within a 30% spread ($83/$91/$97 is one stream; $9.99/$15.49/$22.99 stay three). Two aligned cycles => `needs_review_insufficient_cycles`, never ready; `ready` needs >= 3 cycles.
- `backend/app/services/recurring_candidate_service.py`: `detect_candidate_streams(transactions, accounts, as_of, lookback_days=400)` returns deterministic records (`candidate_key` = SHA-256 of user, account, merchant, sign, cadence, version, tier), plus `history` coverage (`complete` false when less history exists than requested). Pending, internal transfers, duplicates, non-cash and ownerless accounts are excluded.
- Persistence: `recurring_repository.upsert_detected_candidate` (created / updated / preserved) keyed by `(user_id, candidate_key)`; migration `c4f8a1d3e5b7` adds `recurring_streams.candidate_key` + `uq_recurring_streams_user_candidate` (applied to dev Postgres; downgrade/upgrade round-trip verified). A rescan never overwrites confirmed / ignored / ended; evidence is append-only.
- `/api/recurring/scan/<account_id>`: owner-checked adapter over `load_v2_source_data` (canonical sign normalized once there; no `display_transaction_amount`), `lookback_days` 30-1000 (default 400), no Plaid calls, no fabricated Transactions; response = legacy reminders + `scan{created,updated,preserved,candidates,history_days,history_incomplete,sign_excluded}`.
- `RecurringDetector` / `RecurringBridge` are compatibility wrappers over the canonical engine and repository.
- Tests: `tests/test_recurring_detection.py` (18: utility, biweekly payroll, semimonthly, quarterly, yearly, month-end clamp, tiers, exclusions, key stability, legacy wrapper, route regression with 3 x $700 on Jul/Aug/Sep 21 -> one stable monthly candidate due Oct 21, 2 occurrences review-only, ignored stays ignored, memo-digit change does not split, foreign account 404, no owner 503); forecast V2 suites unchanged (one test updated: yearly is now a supported cadence). Real-data read-only check: 36 candidates from 1,907 rows in 0.39s.
- Automatic recomputation: no safe idempotent hook exists in the sync pipeline, so manual rescan (`POST /api/recurring/scan/<account_id>`, surfaced by TP-005) is required; nothing claims automatic recomputation and no scheduler was added.
- Deviations: `tests/test_recurring_bridge.py` remains skipped (needs the full application); wrapper behavior is covered in `test_recurring_detection.py`. Changing bank-memo *words* (not just reference digits) produces a different merchant key; that is existing `normalize_merchant_key` behavior and out of scope.
