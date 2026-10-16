# TP-20261016-007: Accounts Classification and Financial Coverage Integrity

**Packet ID:** TP-20261016-007  
**Status:** Ready  
**Created:** 2026-10-16  
**Last updated:** 2026-10-16  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-007-account-classification-coverage-truth.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P0  
**Depends on:** None  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Accounts Classification and Financial Coverage Integrity. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `frontend/src/utils/accountPortfolio.js`
- `backend/app/services/account_portfolio_metrics.py`
- `backend/app/models/account_models.py (read only)`
- `backend/app/routes/accounts.py (serialize existing type fields if missing)`
- `frontend/src/components/accounts/AccountPortfolioOverview.vue`
- `frontend/src/components/accounts/AccountPortfolioList.vue`
- `frontend/src/utils/__tests__/accountPortfolio.spec.js`
- `tests/test_account_portfolio_metrics.py`
- `frontend/src/components/accounts/__tests__/AccountPortfolio.spec.js`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
`classifyAccount()` currently returns investment immediately if `account.is_investment`, BEFORE examining explicit type/subtype. Screenshot groups `Robinhood Credit Card` and `Robinhood Savings` into Investments; flags may be mismapped. Overview headline excludes hidden accounts (screenshot says 17 hidden); risk of presenting incomplete net position as comprehensive. Existing metrics calculate assets/liabilities/utilization and known-limit denominator.

## Required code edits, in order
1. `accountPortfolio.js:classifyAccount` classify explicit account `type` and `subtype` aliases credit/loan/depository BEFORE legacy `is_investment`; `is_investment` applies only when no conflicting explicit type/subtype or recognized investment subtype. Normalize `brokerage|ira|401k` investment. If conflicting `is_investment=true` and `type='credit'`, classify credit AND surface `classification_conflict` in debug/coverage metadata (not visible alarm in normal rows). Keep output group keys and existing sorting/filtering API.
2. `backend/app/services/account_portfolio_metrics.py` align classification precedence with frontend; use normalized assets/liabilities semantics already implemented. Do NOT rewrite Plaid `is_investment` flags indiscriminately without provider source proof; audit origin in `backend/app/sql/account_logic.py` and record mapping correction only if demonstrably wrong at ingestion.
3. `AccountPortfolioOverview.vue` display clear scoping line e.g. `11 visible of 28 linked; 17 hidden excluded` and separate `known credit limits: 2/4 cards`. Distinguish known-assets coverage from `no data`; if hidden accounts excluded, label net position `Visible-account net` / `Partial net position` rather than unqualified total. Never merge currencies silently.
4. `AccountPortfolioList.vue` ensure group ordering then institution, correct account type label and debt/credit utilization only for true card rows; default filters preserve selection on classification change.

## Exact contracts and acceptance fixtures
- A `Robinhood Credit Card` with explicit credit type/subtype and `is_investment=true` must classify credit, not investment; `Robinhood Savings` type depository likewise. IRA investment remains investment.
- Totals and chips agree after type correction; if hidden accounts excluded, warning is concrete and no phantom zero balance.

## Validation commands
`cd frontend && npm run test -- --run src/utils/__tests__/accountPortfolio.spec.js src/components/accounts/__tests__/AccountPortfolio.spec.js`; `pytest tests/test_account_portfolio_metrics.py -q`; group summary reconcile. No migration required unless source mapping genuinely wrong.

## Non-goals
No Plaid relink or new account products. No estimating missing balances or undisclosed credit limits.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.
