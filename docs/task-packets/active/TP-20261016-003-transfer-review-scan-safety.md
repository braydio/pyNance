# TP-20261016-003: Transfer Matching Security, Scope, Evidence and Review

**Packet ID:** TP-20261016-003  
**Status:** Ready  
**Created:** 2026-10-16  
**Last updated:** 2026-10-17  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-003-transfer-review-scan-safety.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P0  
**Depends on:** TP-20261016-001  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Transfer Matching Security, Scope, Evidence and Review. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `backend/app/routes/transactions.py`
- `backend/app/services/internal_transfer_review.py (new)`
- `frontend/src/components/transactions/InternalTransferScanner.vue`
- `frontend/src/views/Transactions.vue`
- `frontend/src/services/api.js`
- `tests/test_internal_transfer_detection.py`
- `tests/test_transfer_analytics_exclusion.py`
- `frontend/src/components/transactions/__tests__/InternalTransferScanner.spec.js (new)`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
`POST /api/transactions/scan-internal` currently queries every non-internal/nonpending Transaction+Account, groups ALL users in-process and returns matched candidates from all groups; `allow_same_account` defaults true. Matching is offsetting amount +/- within 3 days; raw `match_score` is smaller-is-better yet shown without explanation. UI tab label `Scanner` hides what it does; `Mark Internal` confirms a pair with no matched-source explanation. Existing `PUT /api/transactions/update` must ensure both rows are same-owner before `flag_counterpart`.

## Required code edits, in order
1. Extract existing `_internal_match_score` and matching loop to `internal_transfer_review.py:find_candidates(owner_id, start_date,end_date, account_ids, max_rows=2000, allow_same_account=False)`. Filter *in SQL* by bound trusted owner AND account owner, posted, not marked internal, bounded date range default 90 days, indexes `(user_id,date)`; query fails closed without trusted identity. Hard cap range 365d, 2000 rows/query and 100 candidate pairs; pagination or informative truncation flag. Don't leak candidate user identifiers or source raw PII.
2. Use canonical account delta from 001 for optional explanation, but matching equality/opposite should compare normalized comparable signs; if ambiguous sign skip. Default same-account matching false; exceptional same-account corrections require explicit opt-in and stronger evidence. Keep scoring for sort but return `{pair_id, left:{transaction_id,date,account_label,merchant,amount}, right:..., evidence:{amount_gap_cents,day_gap,shared_tokens,transfer_keyword,low_confidence}, confidence_label:'strong|review'}`; labels are rule based, not guessed numeric percentages. Preserve existing top-level `pairs` array or adapt client/tests atomically.
3. `PUT /api/transactions/update` validation: verify requested transaction and counterpart share trusted owner, account ownership, opposite signs, unchanged pending state, and one-to-one linkage before marking BOTH `is_internal` and `internal_match_id`. Add idempotency/replay safe confirmation; reject cross-owner pair 403 without partial changes.
4. `InternalTransferScanner.vue` label `Transfer Review` in `Transactions.vue` tabs, introduce one-sentence purpose, last scan range, results count, paired transaction cards, evidence bullet, Confirm Pair and Not a Transfer (nonpersistent dismissal in this packet), done/error state. Avoid raw match score/time_delta_hours-only UX; no automatic mutation on scan.

## 2026-10-17 correction: one-sided movement is not recognized income
A daily dashboard modal showed a +$200 self-Zelle account transfer and a +$100 brokerage-labeled inflow counted as $300 Income. This is a **reporting classification defect even before a reciprocal pair is found**. Pair detector here remains evidence-based and must not fabricate a pair or mutate `is_internal` on an unmatched row. Preserve category/source evidence and user correction for the read-only classifier in TP-20261017-003; a likely one-sided owned transfer goes to neutral `transfer` if supported, uncertain deposits go to `unclassified` review, **not automatic income**. Wire confirmed pair changes to reporting cache invalidation for chart/modal TP-20261017-004. Do not duplicate their reporting computation inside this packet.

## Exact contracts and acceptance fixtures
- GET-like scan remains POST but read-only; cannot scan across tenants. No candidates on missing auth. Same-account refund does not auto-classify as transfer. Confirm requires both in-scope IDs.
- Paired transfers are excluded from income/spending when confirmed, but should remain auditable transaction records.

## Validation commands
`pytest tests/test_internal_transfer_detection.py tests/test_transfer_analytics_exclusion.py -q`; add unauthorized, cross-user, pending, amount mismatch, duplicate-confirm and large-input cutoff fixtures. `cd frontend && npm run test -- --run src/components/transactions/__tests__/InternalTransferScanner.spec.js && npm run build`.

## Non-goals
No general transaction anomaly detector; no automatic transfer flagging; no global session-auth redesign, but fail closed where owner isn't trusted.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.
