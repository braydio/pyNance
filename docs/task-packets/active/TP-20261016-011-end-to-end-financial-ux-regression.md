# TP-20261016-011: Cross-Page Financial Truth and Interaction Regression Gate

**Packet ID:** TP-20261016-011  
**Status:** Ready  
**Created:** 2026-10-16  
**Last updated:** 2026-10-16  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-011-end-to-end-financial-ux-regression.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P1  
**Depends on:** TP-20261016-001 through TP-20261016-010  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Cross-Page Financial Truth and Interaction Regression Gate. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `tests/forecast_v2_world.py`
- `tests/test_forecast_v2_api.py`
- `tests/test_forecast_v2_validation.py`
- `tests/test_routes_recurring.py`
- `tests/test_internal_transfer_detection.py`
- `tests/test_account_portfolio_metrics.py`
- `frontend/cypress/e2e/transactions.cy.js`
- `frontend/cypress/e2e/forecast-v2.cy.js`
- `frontend/cypress/e2e/accounts.cy.js`
- `docs/frontend/FINANCIAL_WORKFLOWS_QA_2026-10-16.md (new)`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
Previous TP-20261014-022 UI QA marked complete before this feature redesign. This gate tests corrected finance semantics and three-page user journeys after new backend/contracts land, not another generic styling sweep.

## Required code edits, in order
1. Add fixture world with 2 checking, savings, credit card, broker/IRA, 17 hidden accounts, ambiguous manual transaction, real Plaid sign fixture, 3 similar recurring merchant charges, month-end utility, annual fee, credit-card purchase+checking settlement, transfer pair, unverified APR. One fixed local as-of 2026-10-16 (or tests freeze date), no live Plaid calls.
2. `pytest` scenario: source raw +purchase gets negative cash effect, income positive, credit charge not twice deducted; current+future cash reconciles for known scheduled debt; unknown liability shows missing coverage not invented payment; two recurrence scans idempotent, ignored candidates remain ignored; no phantom transactions; `/scan-internal` cross-owner access fails; account investment flag conflict classified correctly and hidden excluded totals labeled.
3. `Cypress` three routes /accounts,/transactions,/forecast across 390/768/1280, Nightfox/Everforest, data+empty+error. Activity insights full matching vs visible 10/page; Recurring confirm -> forecast driver appears once and variable spending residual adjusted; Transfer Review confirm -> no double counted income; Accounts long institution + Connections cards theme; Forecast 100 residual events compact and signed currency. Verify keyboard, two-theme contrast, drawer/popover focus, no document horizontal scroll. No paid vendor APIs.
4. Write `docs/frontend/FINANCIAL_WORKFLOWS_QA_2026-10-16.md`: exact tests run, fixture ids scrubbed, per-route PASS/FAIL/BLOCKED and screenshot paths; if local backend/db unavailable mark unverified rather than declaring success. Fix regressions only within named earlier packet ownership, no new design directions.

## Exact contracts and acceptance fixtures
- Pass requires no incorrect sign, no duplicate debt settlement, no cross-user leak, no accidental recurring auto-confirm and no fake ledger source.
- Previously completed UI packet statuses remain intact; this is the post-feature verification gate.

## Validation commands
`pytest tests/test_transaction_semantics.py tests/test_recurring_detection.py tests/test_routes_recurring.py tests/test_internal_transfer_detection.py tests/test_forecast_v2_api.py tests/test_forecast_v2_validation.py tests/test_account_portfolio_metrics.py -q`; `cd frontend && npm run test -- --run && npm run lint && npm run build`; execute Cypress with configured backend, record blocker if unavailable.

## Non-goals
No unrelated page audit (Planning/Investments/Settings deferred until later user review).

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.
