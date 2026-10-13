# TP-20261013-002: Forecast V2 Core: Event Ledger + Liquidity Semantics

**Packet ID:** TP-20261013-002  
**Status:** Ready  
**Created:** 2026-10-13  
**Last updated:** 2026-10-13  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261013-002-forecast-v2-core-event-ledger.md`  
**Workstream size:** One implementation packet  
**Depends on:** None (forecast-series phase 1 of 4)  
**Priority:** High  
**Series:** Forecast V2, packet 1 of 4 (execute 002 -> 003 -> 004 -> 005)  


## Objective

Create a deterministic, account-safe, event-driven **liquid-cash** projection core. Each day carries dated scheduled inflows/outflows and explicit adjustments, including zero-transaction days. Separate cash liquidity, liabilities, investment valuation, and net worth. Ship a pure V2 computation contract with standalone tests; **do not switch the live frontend or legacy endpoint yet**. Preserve old Forecast V1 calculation until TP-20261013-005 opts into V2.

## Confirmed seams on main (2026-10-13)

- `backend/forecast/engine.py::project_balances` gets snapshots and average daily inflows/outflows, then applies the same net delta each day:
  ```python
  current_balance += average_inflow - average_outflow
  ```
  `compute_forecast` calls this, then `apply_adjustments` and `build_cashflow_items`. Recurring sources in `_recurring_sources_by_date` primarily **attribute** the existing delta; they do not drive its magnitude.
- `backend/forecast/engine.py::_build_adjustment_schedule` already supports once/weekly/monthly and distributed-range adjustments; preserve V1 semantics and reuse sound helpers.
- `backend/forecast/models.py` provides `ForecastTimelinePoint`, `ForecastCashflowItem`, `ForecastSummary`, and `ForecastResult` with serialization. Extend, do not fork the model definitions.
- `backend/app/routes/forecast.py::_load_latest_snapshots` uses `AccountHistory` / `Account`; `_snapshot_balance_breakdown` subtracts liabilities; `_load_historical_aggregates` filters `Transaction.is_internal`. Do **not** treat the existing mixed net-worth balance as liquid cash.
- `backend/app/models/account_models.py::Account` has `type`, `subtype`, `is_investment`, `balance`, `user_id`, `is_hidden`; `AccountHistory` is dated per account. `Transaction.amount` is signed numeric in `backend/app/models/transaction_models.py`.

## Locked architecture & contracts

**New module:** `backend/forecast/v2_core.py` (pure Python, no DB calls), plus extend `backend/forecast/models.py` with typed `ForecastV2Event`, `ForecastV2DailyPoint`, `ForecastV2Result` or equivalent explicit dataclasses. Export only JSON-safe fields.

Event contract, not a DB migration:
```python
{
  "event_id": "manual:rent:2026-11-01",
  "date": "2026-11-01",
  "amount": "-1850.00",      # signed cash effect, Decimal internally
  "account_id": "cash-checking",
  "kind": "scheduled_bill", # scheduled_income, scheduled_bill, adjustment, residual
  "source_id": "bill-123", "source": "recurring", "confidence": 0.95,
  "metadata": {"category": "housing"}
}
```
`source_id` and `event_id` must be stable for identical inputs, used to dedupe exact event instances; do not collapse distinct legitimate same-day payments. A debit is negative and a deposit positive **in the V2 event model**. Normalize incoming transaction/provider signs once at the adapter boundary; never infer cash direction solely from vague categories.

`ForecastV2DailyPoint` contract:
```python
{
 "date":"2026-11-01", "starting_cash":3000.00,
 "inflows":200.00, "outflows":1850.00, "adjustments":0.00,
 "ending_cash":1350.00, "event_ids":[...],
 "liability_balance":4200.00, "investment_value":5000.00,
 "net_worth":2150.00
}
```
The exact optional breakdown fields may evolve but **cash and net worth cannot share one ambiguous field**. Always create a point for every calendar day, including weekends/zero-event days. Define starting balance as EOD balance at the **day preceding first projected date**; events on day 1 apply once. Numerical invariants: `ending_cash=starting_cash+inflows-outflows+signed_adjustments`, next day's start=previous day's end, `net_worth=liquid_cash+other_noninvestment_assets+investments-liabilities` for included accounts. Use Decimal internally and round only at serialized currency boundaries; reconciliation tolerance <= $0.01.

**Account policy:** liquid-cash base includes eligible depository accounts only (checking, savings, cash) by explicit normalized type/subtype; credit, loans and investments are separate buckets. Unknown account types are excluded from liquid cash and surfaced as data-quality warnings, never silently assumed cash. Hidden/excluded accounts and unauthorized accounts must not enter any bucket. Differentiate cash-to-cash transfers (zero combined liquid-cash impact) from cash payments to a liability (cash decreases, liability decreases; not a net-worth expense). Purchases charged to credit are **not** checking-account cash outflows until paid. This packet defines/classifies these flows; it does not build a full debt amortization engine.

**Schedule semantics:** implement pure calendar expansion from explicit inputs:
- `once`, `daily`, `weekly`, `biweekly` (14 days), `semimonthly` (two explicit month days), `monthly`.
- Monthly day 29/30/31 clamps to last valid day with an original anchor day, then returns to anchor next month. Leap years handled. Invalid cadence/date rejected with specific errors, not silently dropped.
- Recognize effective start/end dates; no retroactive events outside horizon.
- Handle duplicate source-event instance IDs deterministically; support manual overrides without double-applying an event.

Pure public entrypoint recommendation:
```python
def simulate_cash_ledger(*, start_date, horizon_days, account_snapshots,
                         events, cash_adjustments=(), assumptions=None) -> ForecastV2Result:
    # normalize/validate owner-free inputs -> sort by (date,event_id)
    # expand calendar instances -> bucket by day -> ledger+summary+provenance
```
Separate event expansion function e.g. `expand_scheduled_events` and account classifier `classify_forecast_account` so Packet 003 can reuse them. Do not read wall-clock time inside simulation; explicit dates and inputs are required.

## Required work / order

1. Define dataclasses/schema and pure event-expansion functions in `backend/forecast/models.py` and `backend/forecast/v2_core.py`; include strongly documented signed amount conventions.
2. Add normalized asset/liability/investment/cash partitioning helpers without changing existing `_snapshot_balance_breakdown` behavior used by V1.
3. Implement cash daily ledger and derived minimum/ending balances, date of first negative cash, cashflow attribution and safe provenance.
4. Return explicit missing/stale/unknown-data flags; avoid claiming precision from unknown holdings. Keep a deterministic `baseline` output for later scenario/uncertainty layers.
5. Add `docs/backend/forecast/v2_core.md` (new module documentation) and update `docs/forecast/FORECAST_ROADMAP.md` with phase status when implemented.

## Required tests

Add `tests/test_forecast_v2_core.py`; extend `tests/test_forecast_engine.py` only for compatibility/invariants.

- Three liquid accounts, two liabilities, one investment -> correctly partition cash vs net worth; subset of accounts changes only matching buckets.
- EOD anchor (day 0) + rent on day 1, payday day 3, all intervening zero-days; each event applies exactly once.
- Cash-to-cash transfer has no consolidated liquidity effect; credit-card payment lowers cash and liability, not net worth twice; credit purchase not a checking cash event.
- Semimonthly, biweekly, Jan 31 -> Feb 28/29 -> Mar 31, crossing year end; no drift.
- Manual one-time/recurring/distributed adjustments run once and preserve daily invariant; duplicate event IDs deduped, distinct events retained.
- Two runs with the same inputs produce byte-equivalent serialized results; event provenance traceable.
- Unknown types, invalid dates/cadences, negative horizon, no eligible cash account handled explicitly.
- Existing `compute_forecast` and legacy API contracts still behave as before.

Commands:
```bash
pytest tests/test_forecast_v2_core.py tests/test_forecast_engine.py -q
pytest -q
python scripts/check_docs.py --changed-since origin/main
```

## Acceptance criteria

- [ ] Pure event-to-ledger V2 module and typed result exist, with comprehensive daily coverage and cent-level reconciliation.
- [ ] Correct liquid-cash, debt and investment semantics (no mixed-balance liquidity projection).
- [ ] Calendar recurrence and adjustments are deterministic and correctly anchored.
- [ ] Account and event ownership/scoping contract is explicit for Packet 005 adapter; no user data leaks.
- [ ] Unit tests cover transfers, credit payments, calendar rollover and missing data.
- [ ] V1 routes/frontend remain unmodified/working.
- [ ] Documentation and exact validation outcomes recorded.

## Non-goals

No live API switch, frontend redesign, recurrence inference, Monte Carlo, persistent scenarios, ARIMA training, debt interest/amortization, DB migration, or speculative investment returns.

## Handoff / dependencies

Next packet: TP-20261013-003 (Recurring Detection + Residual Spending). It imports V2 event model/ledger, and **must not invent a parallel forecast result type**.

## Completion report

Report as `Workstream: TP-20261013-002`; Status, commit URL, validation results, tested ledger invariants, new contracts, known issues and next packet.

## Execution rules (AGENTS.md)

Implement from this canonical packet, not old docs. Check the packet tracker and only the listed symbols against latest `main`; mark packet and tracker `In Progress` when starting. On completion, run tests, set `Complete`, move the packet to `completed/`, and update INDEX/TRACKER in the same commit. Keep local/origin `main` synchronized without force-push and report exact tests, deviations, blockers, and commit URL. Do not fabricate the authoring chat URL.

