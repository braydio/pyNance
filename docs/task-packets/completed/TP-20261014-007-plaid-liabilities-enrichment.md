# TP-20261014-007: Optional Plaid Liabilities APR and payment metadata

**Packet ID:** TP-20261014-007  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261014-007-plaid-liabilities-enrichment.md`  
**Workstream size:** One independently testable implementation packet  
**Depends on:** TP-20261014-005, TP-20261014-006  
**Priority:** Normal  
**Series:** Accounts audit 3 of 5  
**Audited paths:** Accounts frontend and backend on 2026-10-14; prior head d38bd3d  

## Objective
Optional Plaid Liabilities APR and payment metadata. Implement against current main with no repository-wide rediscovery.

## Current state and exact implementation

**Current seams**
- `backend/app/helpers/plaid_helpers.py:get_accounts` fetches /accounts/get; no existing `liabilities_get` adapter.
- `backend/app/routes/accounts.py:_plaid_products_for_account`, `refresh_all_accounts`, `refresh_single_account` dispatch transactions/investments; other enabled products skipped.
- `backend/app/sql/account_logic.py:canonicalize_plaid_products` already stores item-scoped enabled scopes; `backend/app/routes/plaid_transactions.py` owns Link product consent.
- Official schema: https://plaid.com/docs/api/products/liabilities/ and https://plaid.com/docs/api/accounts/. Credit cards have multiple `aprs[]` by type, can have empty APRs; loans and lines have distinct rates and due dates. Not all Items have consent/entitlement.

**Implement**
1. New `backend/app/services/plaid_liabilities.py`: installed SDK `LiabilitiesGetRequest` or compatible typed request, one authorized `/liabilities/get` per Item, only if current persisted scopes contain `liabilities`; batch match account_id to owner and connected PlaidItem; reject cross-item ownership. No forced consent scope/cost escalation and no per-account duplicate remote calls.
2. Hook Item adapter into existing refresh orchestrator `backend/app/routes/accounts.py` with existing rate limit, reconnect and error aggregation. If unavailable/unauthorized mark rate metadata unavailable/stale, continue other accounts/products; no silent zero APR or claim "live".
3. Store `apr_details` buckets individually (`purchase_apr`, `cash_apr`, `balance_transfer_apr`, `penalty_apr`, `special`). Populate legacy Account.apr ONLY for a genuine purchase APR; provider source wins over inferred. Do not collapse penalty/cash APR into purchase. Store loan fixed/variable rate separately from credit card APR, optional minimum due, due date, statement balance/date, available credit and limit as available. If schema extension needed, add a verified-head Alembic revision and doc. Ignore unknown product response safely.
4. Add additive scoped fields to `backend/app/routes/accounts.py:list_accounts`: `interest_rate_breakdown`, `rate_status`, `minimum_payment_amount`, `next_payment_due_date`, `statement_balance`, `statement_date`, source/as-of, nulls when absent. No credentials/PII leakage. Clarify cached Plaid data vs actual real-time.

**Tests** New `tests/test_plaid_liabilities_enrichment.py` using mocked SDK: eligible product, none, empty APR list, two APRs on same card, loan vs card, same Item two accounts but one call, cross-owner mismatch rejected, webhook/reauth failure, partial status. Run `pytest -q tests/test_plaid_liabilities_enrichment.py tests/test_accounts_product_scopes.py tests/test_plaid_connection_health.py`.

**Non-goals** Do not automatically enable Liabilities or create a paid real-time Balance request; no universal issuer coverage. **Accept:** legitimate scoped provider data only; provider APR/source and due information typed and accurate.


## Implementation order and closeout
1. Check `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate named seams only.
2. Mark In Progress in packet and tracker. Complete changes in order listed; run focused tests then lint/build/available guards. For migrations verify dev DB target and live revision head first.
3. On pass mark Complete, move packet to completed/, update INDEX/TRACKER in same change, commit only packet-owned changes to origin/main with normal synchronization; never force push.
4. Report files changed, contracts, tests (honestly), screenshots if UI, deviations and exact blocker/resume condition.

## Do not rediscover
Avoid broad repo archaeology. Only inspect explicitly named paths, directly imported helpers/tests, and exact migrations/route registrations needed to implement this packet.

## Completion report

- New `app/services/plaid_liabilities.py` (+ doc): scope-gated, one `/liabilities/get` per Item via the installed SDK `LiabilitiesGetRequest`, per-bucket APR storage, loan rates kept separate, cross-item/cross-owner rejection, safe handling of consent/reauth/network errors.
- `routes/accounts.py`: `_refresh_plaid_liabilities` hooked into bulk and single refresh (existing throttle/reauth/error aggregation; failures do not stop other accounts/products). `list_accounts` adds `interest_rate_breakdown`, `rate_status`, `rate_source`, `rate_as_of`, `minimum_payment_amount`, `next_payment_due_date`, `statement_balance`, `statement_date`.
- Migration `c3e7f9a1d5b4` (revises `b2d6e8f0c4a3`) + doc for the six nullable metadata columns.
- Tests: new `tests/test_plaid_liabilities_enrichment.py` (11, mocked remote call); with `test_accounts_product_scopes.py`, `test_plaid_connection_health.py` and the 005/006 tests: 53 passed. ruff/black clean.
- Deviations/not run: webhook-driven refresh not added (not in scope); migration not run against a live dev DB; no live Plaid call (sandbox credentials unavailable here).
