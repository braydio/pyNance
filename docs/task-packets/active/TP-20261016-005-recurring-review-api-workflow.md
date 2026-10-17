# TP-20261016-005: Recurring Review API, Durable Decisions and Usable UI

**Packet ID:** TP-20261016-005  
**Status:** Ready  
**Created:** 2026-10-16  
**Last updated:** 2026-10-16  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-005-recurring-review-api-workflow.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P1  
**Depends on:** TP-20261016-002, TP-20261016-004  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Recurring Review API, Durable Decisions and Usable UI. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `backend/app/routes/recurring.py`
- `backend/app/services/recurring_repository.py`
- `backend/app/__init__.py (only if new Blueprint; prefer existing)`
- `frontend/src/api/recurring.js`
- `frontend/src/components/recurring/RecurringTransactionSection.vue`
- `frontend/src/views/Transactions.vue`
- `frontend/src/components/planning/PlanningSummary.vue (only read consumer if existing)`
- `tests/test_routes_recurring.py`
- `frontend/src/components/recurring/__tests__/RecurringTransactionSection.spec.js (new)`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
`RecurringTransactionSection.vue` defaults `accountId = route.params.accountId || '1'` while `/transactions` has no accountId route parameter. Manual Save stops if Transaction ID empty, and form sends no `tx_id`. Existing detected reminders only show next seven days; no inventory/review states; Transactions prefill writes child refs directly without switching to Recurring tab.

## Required code edits, in order
1. Add owner-safe REST to existing `/api/recurring`: `GET /streams?status=&account_id=&page=&page_size=` (20-100), `GET /candidates?account_id=&include_ignored=false`, `POST /scan` body `{account_ids?,lookback_days?:400,dry_run?:true}`, `POST /streams` manual create, `PATCH /streams/<stream_id>` adjust account, amount/cadence/date/notes, `POST /streams/<stream_id>/decision` `{decision:'confirmed'|'ignored'|'ended'}`, `DELETE /streams/<stream_id>` soft end by default; responses stable `{stream_id,status,source,cadence,amount_cash_delta,amount_range,next_due_date,confidence,evidence_count,reason_codes,...}`. Trusted owner must be resolved server-side (as 002), 404 foreign IDs; scan is readonly by default and optionally records proposed candidates atomically with 004.
2. Update `frontend/src/api/recurring.js` wrappers to above; keep old endpoints as compatibility without relying on undocumented `reminders` for full list. No user-visible raw transaction IDs required.
3. Rewrite `RecurringTransactionSection.vue`: `accountId` prop OPTIONAL, default `All accounts`, account picker from already-known data; remove hardcoded `1` and required transaction ID; async load from `/streams` and `/candidates`; sections `Needs review`, `Confirmed & upcoming`, `Ignored/Ended` collapsed. Each candidate: merchant, amount range, cadence, next predicted date, 2-5 evidence rows, explanation, actions Confirm / Edit / Not recurring. Confirmation persists and updates everywhere; manual entry can be account + name + amount + date without linking an existing transaction. Use actual `formatAmount`, aria labels/error/loading/empty.
4. `Transactions.vue:prefillRecurringFromTransaction` switch `activeTab='Recurring'` then call child's *explicit* `openFromTransaction(tx)` exposed with `defineExpose`, not mutation of child refs. Reuse planned dashboard/Planning consumer read from confirmed streams, not new duplicate model. Treat all bank transaction ID/candidate evidence as sensitive.

## Exact contracts and acceptance fixtures
- Annual/quarterly and variable amount options match 004. Suggestions NEVER equal confirmed bills until user confirms, unless explicit high-confidence automatic policy later designed.
- Manual created without source tx; ignoring candidate persists after scan; changing account of confirmed stream checks new account owner.

## Validation commands
`pytest tests/test_routes_recurring.py tests/test_recurring_detection.py -q`; `cd frontend && npm run test -- --run src/components/recurring/__tests__/RecurringTransactionSection.spec.js src/views/__tests__/Transactions.spec.js && npm run build` plus e2e 390/1280 UX.

## Non-goals
No forced auto-confirmation, no external API charges, no scheduler. Do not delete original Transaction records when stream ends.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.
