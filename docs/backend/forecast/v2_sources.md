---
Owner: Backend Team
Last Updated: 2026-10-14
Status: Active
---

# Forecast V2 Sources (Recurrence + Residual Spending)

## Purpose

Turns transaction history into inputs for the V2 ledger (`docs/backend/forecast/v2_core.md`) without
double counting: promoted recurring cashflows (paychecks, rent, subscriptions) become dated events
and are removed from the variable-spending average. V1 routes (`_auto_wage_adjustments`,
`_load_historical_aggregates`) are untouched.

| Module | Role |
| --- | --- |
| `backend/forecast/v2_sources.py` | Pure pipeline: `build_v2_inputs`, `normalize_merchant_key`. |
| `backend/app/services/forecast_v2_sources.py` | DB adapter: `load_v2_source_data`, `build_user_v2_inputs`. |

## Pipeline

1. **Scope.** Only caller-authorized accounts are used (transactions on other accounts are rejected
   even if supplied). Rows dated after `as_of_date` or before the lookback window (default 120 days)
   are ignored and counted under `reconciliation.rejected`. No look-ahead.
2. **Buckets.** Every in-scope transaction lands in exactly one bucket and appears once in
   `allocation_audit`:
   `scheduled`, `residual`, `transfer`, `duplicate`, `pending`, `unclassified`.
   - Repeated `transaction_id` -> `duplicate`. Pending rows -> `pending` (`booked_equivalent_exists` or
     `not_posted_yet`). `is_internal` / `internal_match_id` / `transfer_type` -> `transfer` with
     `transfer_kind` (`cash_to_cash`, `liability_payment`, ...). Investment/other accounts ->
     `unclassified` (`non_cash_account`).
   - Credit-account purchases stay in `residual` as the cash-spend proxy; the cash-to-card payment is
     a `transfer`, so household spending is not counted twice and the liquidity effect is kept.
3. **Streams (precedence manual > saved rule > inferred).** Manual rules (`status` active/confirmed/
   disabled) and saved `RecurringTransaction` rules claim matching history by `merchant_key`
   (+ optional `account_id`) or `source_transaction_ids`, and suppress inference for the same stream.
   Unsupported saved cadences (for example yearly) are reported as `unsupported`, never guessed.
   Inference groups by account + merchant + sign, then splits by amount cluster (default +/-15%) so two
   subscriptions at one merchant stay separate. Cadence detection: weekly, biweekly, semimonthly,
   monthly (day-of-month tolerance +/-3 days, month-end clamp aware). Median amount. A lone
   transaction is never a bill.
4. **Promotion.** A stream is projected only with `>= 3` dates and confidence `>= 0.6`
   (heuristic, **not** a calibrated probability), or when its id is in `confirmed_source_ids`.
   Weaker streams are `proposed` (visible in `proposed_rules`, history stays in `residual`).
   Streams with no recent occurrence are `lapsed`. `disabled_source_ids` stop projection; their
   history is treated as ordinary residual.
5. **Events.** Promoted streams expand through `forecast.v2_core.expand_scheduled_events`
   (same calendar semantics). Card-account streams carry no `account_id` (consolidated cash).
6. **Residual model.** On the de-recurred, transfer-cleaned posted set over the **complete** day grid
   (zero days included), per weekday winsorized mean (5%/95%) of daily spend and daily income,
   kept separate (`residual:spend:*`, `residual:income:*` events). Weekdays with `< 4` samples use
   the pooled estimate; `< 14` history days yields `insufficient_history` and no residual events.

## Output

`build_v2_inputs(...)` returns `scheduled_events` and `residual_events` (`ForecastV2Event`, feed to
`simulate_cash_ledger(events=...)`), `streams` (per-stream audit: status, origin, cadence, amount,
confidence + level, reason, `source_transaction_ids`, `next_dates`), `proposed_rules`,
`allocation_audit`, `reconciliation` (counts/amounts per bucket, rejected counts), `coverage`
(history days, confidence, residual model status) and `residual_model`.

## Adapter

`build_user_v2_inputs(user_id=..., as_of_date=..., horizon_days=...)` requires `user_id`, reads only
that user's visible accounts, treats `included_account_ids` as a narrowing filter (foreign ids are
ignored and returned as `ignored_account_ids`), uses the latest `AccountHistory` row on or before
`as_of_date` (missing -> `balance: None`, never today's balance) and returns `account_snapshots` for
the simulator. It never writes to the database.

## Tests

`tests/test_forecast_v2_sources.py`, `tests/test_forecast_v2_adapters.py`, `tests/test_forecast_v2_core.py`.
