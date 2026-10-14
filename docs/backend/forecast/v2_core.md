---
Owner: Backend Team
Last Updated: 2026-10-14
Status: Active
---

# Forecast V2 Core (Event Ledger)

## Purpose

`backend/forecast/v2_core.py` is a pure, deterministic liquid-cash projection. It consumes dated
events instead of applying one average daily delta (the V1 behavior in `engine.project_balances`).
It does no database, clock or network access. The V1 engine, routes and frontend are unchanged;
TP-20261013-005 opts the API into V2.

Result types live in `backend/forecast/models.py`: `ForecastV2Event`, `ForecastV2DailyPoint`,
`ForecastV2Result`.

## Entry points

| Function | Role |
| --- | --- |
| `simulate_cash_ledger(*, start_date, horizon_days, account_snapshots, events, cash_adjustments, assumptions, owner_id)` | Build the per-day ledger, summary, applied events and warnings. |
| `expand_scheduled_events(specs, window_start, window_end)` | Turn recurrence rules into dated events. Reused by packet 003. |
| `classify_forecast_account(account)` | Bucket an account: `cash`, `liability`, `investment`, `other_asset`, `unknown`. |

## Ledger contract

- The opening balance is the end-of-day balance of the day **before** `start_date`; events on
  `start_date` apply once. Every calendar day in the horizon (1..3660) gets a point, including
  zero-event days.
- Amounts are `Decimal` quantized to cents at ingestion, so these hold exactly (not just within $0.01):
  - `ending_cash = starting_cash + inflows - outflows + adjustments`
  - next day's `starting_cash` = previous day's `ending_cash`
  - `net_worth = ending_cash + other_assets + investment_value - liability_balance`
- Cash and net worth are separate fields. `cash_by_account` breaks cash out per account.
- Identical inputs serialize byte-identically regardless of input order (events sort by
  `(date, event_id)`).

### Sign conventions

| Kind | `amount` | Cash effect |
| --- | --- | --- |
| `scheduled_income` | positive | + |
| `scheduled_bill` | negative | - |
| `adjustment`, `residual` | signed | signed (`adjustment` is reported in `adjustments`, not inflows/outflows) |
| `transfer`, `liability_payment` | positive magnitude | `account_id` (source) loses, `counterparty_account_id` gains |
| `liability_charge` | positive magnitude | none; liability owed increases |

Provider signs must be normalized once at the adapter boundary. A wrong sign for income or a bill is
rejected with `invalid_amount`.

### Account policy

- Liquid cash is explicit depository checking/savings/cash (and money market / cash management).
  Credit, loans and investments are separate buckets. Unclassifiable types (including depository
  subtypes such as CDs) are excluded and reported as `unknown_account_type`.
- Hidden/excluded accounts, accounts without a balance, and (when `owner_id` is passed) accounts of
  another `user_id` are excluded with warnings. The adapter must still pass only the authenticated
  user's accounts and events; `owner_id` is defence in depth.
- Events must target an included account, or carry no `account_id` (e.g. a card-funded charge with no known funding account), in which case they affect consolidated cash only and appear under `cash_by_account["unassigned"]`. Events naming any other account are dropped with a warning and never applied.
- Cash-to-cash transfers have no consolidated effect and are excluded from inflows/outflows. Paying a
  liability lowers cash and debt (net worth unchanged; overpayment floors debt at 0 and warns). Credit
  purchases are `liability_charge` events and only hit cash when a later payment is scheduled.
  Transfers to investments move value between buckets with no assumed return.
- Liability `balance` is the amount owed (absolute value is used).

### Recurrence

Cadences: `once`, `daily`, `weekly`, `biweekly` (14 days), `semimonthly` (two explicit `days`),
`monthly`. Monthly/semimonthly days clamp to month end and return to the original anchor day the next
month (31 -> Feb 28/29 -> Mar 31), with no drift. Rules start at `anchor_date`, stop at optional
`end_date`, and never produce events outside the horizon. Invalid cadence/date/range/days raise
`ForecastV2InputError` with a stable `code`.

### Duplicates and overrides

`event_id` is `source:source_id:YYYY-MM-DD` (suffix `#2` when two semimonthly days clamp to one date).
Events sharing an `event_id` collapse to one; an event with `override: true` wins. Distinct same-day
events (different ids) are all applied. Events given without an id get a positional id so they are not
collapsed.

## Result

`status` is `ok`, or `insufficient_data` (no daily points) when no eligible liquid-cash account exists.
`summary` holds `starting_cash`, `ending_cash`, `net_change`, totals, `min_cash`/`min_cash_date`,
`max_cash`, `first_negative_date`, start/end net worth, `by_kind`, `event_count` and
`events_outside_horizon`. `warnings` are `{code, message, account_id?, event_id?}` sorted
deterministically. `baseline` is always `true`; later packets layer scenarios and uncertainty on top.
Event `metadata` is passed through JSON-safe with secret-looking keys (`access_token`, `item_id`, ...)
removed.

## Tests

`tests/test_forecast_v2_core.py`. Run with `pytest tests/test_forecast_v2_core.py tests/test_forecast_engine.py -q`.
