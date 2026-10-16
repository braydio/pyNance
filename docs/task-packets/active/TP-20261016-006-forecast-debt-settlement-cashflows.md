# TP-20261016-006: Forecast Debt Payments vs Purchases: Settlement-Aware Cash Ledger

**Packet ID:** TP-20261016-006  
**Status:** Ready  
**Created:** 2026-10-16  
**Last updated:** 2026-10-16  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-006-forecast-debt-settlement-cashflows.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P1  
**Depends on:** TP-20261016-001, TP-20261016-003, TP-20261016-005  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Forecast Debt Payments vs Purchases: Settlement-Aware Cash Ledger. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `backend/forecast/v2_core.py`
- `backend/forecast/v2_sources.py`
- `backend/app/services/forecast_v2_sources.py`
- `backend/app/services/forecast_v2_service.py`
- `backend/app/services/forecast_balance.py (only if v1 bridge uses it)`
- `backend/app/models/account_models.py (read: minimum_payment_amount, next_payment_due_date)`
- `tests/test_forecast_v2_core.py`
- `tests/test_forecast_v2_service.py`
- `tests/test_forecast_v2_sources.py`
- `tests/test_transfer_analytics_exclusion.py`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
V2 models card purchases as residual cash-spend proxies, but excludes transfer pairs from residual. Confirmed checking-to-credit payment should reduce checking cash exactly once, and credit debt also once; blindly adding recurring card payments atop spend proxies double counts. `/api/forecast/compute` responds with outstanding debt under `net_worth`, but no explicit scheduled debt coverage. Liabilities payment metadata (minimum_payment_amount/due date) exists and may be null.

## Required code edits, in order
1. Keep accounting distinct: `cash` liquid bank accounts, `liability` amount owed, `portfolio/net_worth` separate. Credit purchase: `liability_charge` increases owed, cash delta=0; checking -> credit payment: `liability_payment` magnitude positive, cash -magnitude, owed -magnitude; checking->savings same-owner transfer net consolidated cash 0; loan payment cash negative, principal reduction only if actual principal/interest split known, otherwise mark principal unknown.
2. `forecast/v2_sources.py` construct deterministic `liability_payment` events ONLY from confirmed recurring stream linked to a cash funding account + liability destination, or verified paired transfer evidence (003), or user-entered payment rule. Extend stream schema minimally in 002/005 if needed via additive `funding_account_id`, `destination_account_id`, `event_role` ENUM/string (`ordinary_expense|income|liability_payment|transfer`) with validation; do not invent payment from outstanding balance itself. For confirmed credit card purchases, do not also treat purchase as cash outflow if verified payment schedule is used; add explicit `settlement_mode` per card coverage rather than global heuristic, and make unpaired cards use current proxy method with warning.
3. Construct source event identity `(stream_id,date,event_role)` and dedupe once across bank+card matched rows. Preserve payments where only checking debit known but liability not linked as cash expense with destination unknown (no fabricated debt reduction). Existing `simulate_cash_ledger.apply` already supports `liability_payment`; integrate source builder without double application; amount always positive magnitude for movement events. Guard current account balances nonnegative liability floors and transfer scope.
4. `forecast_v2_service.compute_v2_forecast` add additive `metadata.debt_payment_coverage={included:[{stream_id,date,amount,source}],unmodeled_account_count,unknown_payment_account_ids,mode:'settlement|proxy|mixed'}` and event provenance; use no raw account tokens; warnings on incomplete coverage. V1 API unchanged; until robust, V1 old fallback labeled legacy.
5. Add high-fidelity reconciliation fixtures for 2 accounts/card purchase $100, checking payment $100, card interest $8, checking savings $50, no double count; scenario sensitivity and liquidity P10/P90 baseline remain coherent.

## Exact contracts and acceptance fixtures
- Debt balance $12k alone never subtracts $12k from cash; $500 verified scheduled payment subtracts $500 on due date. In mixed coverage, avoid counting $100 purchase and $100 settlement twice; explain scope limits.
- No due date inferred from minimum-payment estimate when source lacks due date; no fake payment.

## Validation commands
`pytest tests/test_forecast_v2_core.py tests/test_forecast_v2_sources.py tests/test_forecast_v2_service.py tests/test_transfer_analytics_exclusion.py -q`; compare cash+debt conservation and no-lookahead backtest. Tests cover partial scope, unknown funding, missing rate.

## Non-goals
No automatic debt payoff optimizer, no modifying account APR/statement balances, no double booking loan principal.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.
