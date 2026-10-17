# TP-20261016-006: Forecast Debt Payments vs Purchases: Settlement-Aware Cash Ledger

**Packet ID:** TP-20261016-006  
**Status:** Complete  
**Created:** 2026-10-16  
**Last updated:** 2026-10-17
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261016-006-forecast-debt-settlement-cashflows.md`  
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

## Completion report (2026-10-17)

- **Accounting kept distinct.** The V2 ledger already applied `liability_payment` (cash down, owed down, floored at zero) and `liability_charge` (owed up, cash unchanged); this packet added the source side. A debt balance alone never moves cash; a verified $500 plan subtracts exactly $500 on its due date and net worth is conserved (cash -500, owed -500).
- **Schema (additive, migration `d5a9b2c7e1f3`, applied to dev Postgres with a downgrade/upgrade round-trip and the CHECK enforced):** `recurring_streams.event_role` (`ordinary_expense|income|liability_payment|transfer`, default `ordinary_expense`, so every existing row is unchanged), `funding_account_id`, `destination_account_id` (FKs to accounts, SET NULL). `recurring_repository.validate_roles` rejects a payment unless the funding account is an owned deposit account, the destination an owned card or loan, the accounts differ and the amount is a cash outflow; foreign accounts 404; other roles may not name funding/destination. `POST/PATCH /api/recurring/streams` accept and return the new fields; updates re-validate.
- **Sources (`forecast/v2_sources.py`, `app/services/forecast_v2_sources.py`).** Payment events come only from a CONFIRMED stream (loaded by `load_v2_source_data`) or a user-entered manual payment rule, and only when funding is an in-scope cash account and the destination an in-scope liability; otherwise the rule is `unsupported` (`payment_accounts_not_in_scope`) and no payment is invented. Minimum-payment and due-date fields are never used to create a payment. Event identity is `(stream_id, date)` with `event_role` in metadata; loan payments carry `principal_split: unknown`, card payments `not_applicable`.
- **No double counting (explicit per-card settlement, no global heuristic).** A card with a verified payment stream is `settled`: its purchases leave the cash-spend residual (audit bucket `liability_charge`) and instead raise the amount owed through per-card `liability_charge` events from the same weekday model; a recurring bill charged to a settled card becomes a scheduled `liability_charge`, not a cash bill. Cards with no schedule keep the existing proxy method. A checking debit with no linked destination stays an ordinary cash bill with no debt reduction.
- **Service (`forecast_v2_service`).** Additive `metadata.debt_payment_coverage = {mode: settlement|proxy|mixed, included[{stream_id,date,amount,source,funding_account_id,destination_account_id}], settled_account_ids, unmodeled_account_count, unknown_payment_account_ids, invalid_payment_stream_ids}`, per-event provenance on `cashflows[].metadata`, and warnings `debt_payments_partial` (mixed coverage) and `payment_plan_out_of_scope`. No tokens or secrets in the payload. V1 untouched.
- **Tests:** `tests/test_forecast_debt_settlement.py` (16: large balance never reduces cash; $500 plan on its due date; net-worth conservation; purchases not also cash spending; the $100 purchase / $100 payment / $8 interest / $50 savings reconciliation with exact cash and owed arithmetic; recurring bill on a settled card; unknown funding; five invalid payment shapes; loan principal unknown; modes; overpayment floor with `liability_overpaid`; pending and post-cutoff rows), `tests/test_forecast_debt_service.py` (15: coverage in the response, provenance, out-of-scope warning, confirmed-only, owner isolation, ten invalid-plan API cases, PATCH re-validation). Existing `test_forecast_v2_*` and `test_transfer_analytics_exclusion` suites unchanged and passing; the no-lookahead validation suite passes.
- **Not done / follow-ups:** (1) the recurring review UI does not yet expose "this is a card or loan payment" (API only); (2) "verified paired transfer evidence" (TP-003) is not turned into payment events automatically, only confirmed plans and manual payment rules; (3) other confirmed ordinary streams are still not loaded into the forecast (that is TP-20261017-001's scope).
