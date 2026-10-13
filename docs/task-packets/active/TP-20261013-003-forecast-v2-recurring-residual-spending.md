# TP-20261013-003: Forecast V2 Spending Intelligence: Recurrence + Residuals

**Packet ID:** TP-20261013-003  
**Status:** Ready  
**Created:** 2026-10-13  
**Last updated:** 2026-10-13  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261013-003-forecast-v2-recurring-residual-spending.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261013-002  
**Priority:** High  
**Series:** Forecast V2, packet 2 of 4 (execute 002 -> 003 -> 004 -> 005)  


## Objective

Convert historical transactions, recurring rules, known bills, and manual assumptions into a **single deduplicated event calendar + residual variable-spending model** consumed by the V2 ledger. Explicitly eliminate double-counting between historical averages and promoted paycheck/rent/recurring cashflows, and between cash-account transfers and spending. The output is deterministic and auditable.

## Confirmed code seams

- `backend/app/routes/forecast.py::_load_historical_aggregates` sums `Transaction.amount` into daily inflow/outflow and excludes `Transaction.is_internal`, but the daily averages used by V1 are not net of selected/promoted recurring expenses.
- `backend/app/routes/forecast.py::_auto_wage_adjustments`, `_auto_rent_adjustments` infer payroll/rent and are appended in `compute_forecast_route`: `merged_adjustments=list(adjustments)+inferred_wage_adjustments+inferred_rent_adjustments`. This is a **double-counting risk**, not a proven exact duplication for every input.
- `backend/forecast/engine.py::build_cashflow_items` and `_recurring_sources_by_date` currently attribute baseline deltas; `_scaled_category_items` rescales source categories. Neither is the V2 transaction classifier.
- `backend/app/models/transaction_models.py::Transaction` has `account_id`, `transaction_id`, `date`, `amount`, `pending`, `is_internal`, `internal_match_id`, `merchant_slug`, `category_slug`, `personal_finance_category`, and `user_modified`. `RecurringTransaction` already stores `transaction_id`, `account_id`, `frequency`, `next_due_date` but may not represent every supported calendar cadence.
- Existing prior design docs: `docs/forecast/FORECAST_ROADMAP.md`, `docs/backend/backend-ToDo/ForecastingToDo.md`. They describe intent; **current code is source of truth**.

## Locked pipeline

Inputs are always scoped by `user_id`, authorized account set, and strict **as_of_date**. Backend data loader must select data with transaction date <= as_of_date and snapshot date <= as_of_date (no look-ahead). Do not access other users' IDs merely because the caller supplied `included_account_ids`.

1. **Classify historical transactions:** preserve raw source references, original provider sign, account type and normalized signed **cash effect**. Exclude `pending` when booked equivalent exists; dedupe by stable transaction ID. Treat `is_internal` / `internal_match_id` as evidence for paired transfers; cash-to-cash transfers are excluded from aggregate household spending, but cash-to-liability payments affect liquidity once and debt once.
2. **Promote recognized scheduled events:** explicit/manual recurring rules take precedence, then existing `RecurringTransaction` records, then vetted inferred payroll/rent/subscriptions. Use source transaction IDs and stable fingerprints (user+account+normalized merchant/category+cadence) as traceability, not to merge separate legitimate subscriptions at the same merchant. Preserve a user override to disable/confirm a proposed recurrence in the input contract. A confirmed rule must suppress duplicate inference for the same stream.
3. **Generate event dates:** reuse `backend/forecast/v2_core.py::expand_scheduled_events` and its calendar semantics. Infer payday phase, monthly anchor and amount from clean *posted* history. Restrict recurrence to sufficient evidence and expose low confidence/unconfirmed proposals rather than silently add a speculative fixed bill to the high-confidence baseline. A lone transaction is not a recurring bill.
4. **Residual set subtraction:** remove all transaction IDs allocated to promoted recurring streams, paired transfers, and duplicates **before** computing variable spending/income averages. Do not simply add rent/paycheck on top of a global historical daily average.
5. **Robust variable spending:** use complete calendar days including zero-transaction days; group by weekday and (when sample sufficient) category, use median/trimmed or winsorized mean to control outliers. Derive daily residual cash flow with confidence/coverage metadata; preserve positive residual income separately from negative spend. On sparse history, fall back to a transparent pooled estimate or zero with `insufficient_history`; never pretend a precise weekday pattern from two samples.
6. **Source-aware reconciliation:** every included historical transaction maps to exactly one bucket: `scheduled`, `residual`, `transfer/excluded`, `duplicate/pending`, or explicitly `unclassified` (no silent disappearance). V2 future daily cashflow = scheduled events + manual overrides + residual expectation (zero exactly when no evidence). No duplicated event IDs, no inflated category subtotals.

## Concrete implementation path

**New modules:** `backend/forecast/v2_sources.py` (pure classification/recurrence/residual model), `backend/app/services/forecast_v2_sources.py` (DB adapter and as-of data loading, when appropriate).

**Integrate with:** `backend/forecast/v2_core.py` from packet 002, `backend/app/routes/forecast.py::_load_historical_aggregates` / `_auto_wage_adjustments` / `_auto_rent_adjustments` as V1 **reference seams only**. Do not modify V1 route behavior in this packet. Use new adapter for V2; avoid global side effects.

Suggested pure interface:
```python
def build_v2_inputs(*, transactions, recurring_rules, manual_rules,
                    accounts, as_of_date, start_date, horizon_days,
                    disabled_source_ids=()):
    return {
      "scheduled_events": [...], "residual_events": [...],
      "proposed_rules": [...], "allocation_audit": [...],
      "coverage": {"history_days":90,"confidence":"medium",...}
    }
```

Use a separate `ForecastV2SourceAudit` model/dict with per-stream status, `source_transaction_ids`, normalized cadence/amount, projected next dates, confidence (heuristic, **not calibrated statistical probability**), override origin, and reason. Do not expose Plaid tokens, item IDs or unrelated account data.

## Implementation order

1. Secure as-of DB access/adapters using existing Account/Transaction/AccountHistory and recurring relationships; require authenticated user-scope for reads. For historical replay, do not substitute today's latest balance.
2. Pure posted-transaction classification, cross-account transfer handling, duplicate/pending rules.
3. Recurrence pipeline with explicit rule precedence and calendar projection; detect payroll/rent with source IDs and user-review proposals.
4. Residual modeling on de-recurring transaction set + complete day grid; output residual events labeled source and coverage.
5. Validate `scheduled+residual` rollup and source allocation audit, document at `docs/backend/forecast/v2_sources.md`.
6. Ensure caller can feed resulting events to Packet 002 simulator without changing V1 frontend/endpoint.

## Regression tests

New `tests/test_forecast_v2_sources.py` and, as needed, `tests/test_forecast_v2_adapters.py`; preserve `tests/test_forecast_engine.py` and `tests/test_forecast_routes.py` if that test exists.

- Historical salary $2,000 every 14 days: one future payday event, salary transactions excluded from residual income; no average+paycheck duplication.
- Monthly rent $1,850 plus ordinary transactions: exactly one future due-date outflow and no duplicated daily rent.
- Same-bank cash-to-cash transfer and cash-to-card payment: no falsely doubled household expense; checking liquidity decrement for card payment is preserved.
- Two legitimate subscriptions to same merchant are not collapsed solely by merchant; duplicate bank transaction import *is* deduped.
- Missing months, month-end dates, user rule disable/confirm, monthly date drift, amount jitter/outlier and holiday/weekend shifted deposits.
- Transaction history with zero-spend weekdays includes zero-days, outliers robustly constrained; sparse dataset flags insufficient confidence.
- Snapshot/transaction dated **after as_of_date** excluded; explicit foreign account ID must not bypass user ownership.
- Audit accounts for every in-scope posted transaction exactly once; daily decomposition reconciles to V2 ledger.

Commands:
```bash
pytest tests/test_forecast_v2_sources.py tests/test_forecast_v2_adapters.py tests/test_forecast_v2_core.py -q
pytest -q
python scripts/check_docs.py --changed-since origin/main
```
If split test files differ, update commands to actual names and record them.

## Acceptance criteria

- [ ] All known/promoted recurring cashflows are projected on calendar dates rather than baked into daily averages.
- [ ] Residual distributions use de-recurring and transfer-cleaned **posted** history and complete calendar-day samples.
- [ ] No duplicate salary/rent or cash transfer expense; accounting audit supports each classification.
- [ ] Strong user/account ownership and as-of isolation; future data cannot influence historical forecast.
- [ ] Event sources and uncertain/disabled proposals are reviewable.
- [ ] Same deterministic inputs generate same events and audit output; no V1 route regression.
- [ ] Focused tests, docs and handoff landed.

## Non-goals

No live frontend switch, Monte Carlo, calibration, persistent rule-review UI, migrations unless unavoidable, full ML anomaly pipeline, or automatic mutation of user transactions/recurring tables.

## Handoff / dependencies

Next: TP-20261013-004 (Probabilities + Backtesting). Input is deterministic baseline from Packet 002 plus scheduled/residual/audit data from this packet. **Do not rediscover** existing routes/models or rewrite `forecast_orchestrator.py` to achieve this.

## Completion report

`Workstream: TP-20261013-003`, status, commit URL, sample replay outcomes, double-count and as-of tests, test commands/results, remaining gaps and next packet.

## Execution rules (AGENTS.md)

Implement from this canonical packet, not old docs. Check the packet tracker and only the listed symbols against latest `main`; mark packet and tracker `In Progress` when starting. On completion, run tests, set `Complete`, move the packet to `completed/`, and update INDEX/TRACKER in the same commit. Keep local/origin `main` synchronized without force-push and report exact tests, deviations, blockers, and commit URL. Do not fabricate the authoring chat URL.

