---
Owner: Backend Team
Last Updated: 2026-10-02
Status: Active
---

# Safe-to-Spend Service (`safe_to_spend.py`)

## Purpose

Build the dashboard's immediate spending guardrail from visible cash accounts, planned bills, a protected buffer, and today's posted outflows.

## Public API

- `SafeToSpendInputs`: normalized service input dataclass for user scope, mode, as-of date, and buffer.
- `build_safe_to_spend_payload(inputs)`: returns an API-serializable decision payload.

## Calculation

```text
raw spend room = spendable cash - upcoming bills - protected buffer - spent today
spend room = max(raw spend room, 0)
```

For `until_payday` and `week`, the service also divides the horizon amount into `per_day_cents`.

## Data sources

- Visible cash-like `Account` records for spendable cash.
- Baseline `PlannedBill` records (the oldest scenario per account; what-if variants are ignored) due in the protection window.
- Owner `RecurringStream` rows (confirmed, plus high-confidence provisional candidates) expanded at read time with `forecast.v2_core.expand_scheduled_events`; see `recurring_obligation_projection.py` below.
- Non-internal outflows on the as-of date for today's spending. Plaid uses positive
  amounts for outflows; other providers retain the legacy negative-outflow convention.
- Recent income-like inflows to infer a likely next payday, using the inverse
  provider-specific sign convention.
- Transaction ownership is scoped through the joined `Account.user_id`, which is
  authoritative when older transaction rows have a null `Transaction.user_id`.

## Edge cases

- Unknown modes fall back to `today`.
- Missing account data yields `confidence: limited` or `estimated` rather than failing the dashboard.
- Negative spend room is clamped to zero and reported as `do_not_spend`.

## Reliability and transaction ownership

Spending uses positive Plaid amounts and negative non-Plaid amounts; income candidates use negative Plaid amounts and positive non-Plaid amounts, followed by the income metadata check. Stored transaction signs remain unchanged. Both transaction queries scope through `Account.user_id`, including transactions whose own `user_id` is null.

The legacy Plaid refresh delegates to the shared upsert, which writes account ownership on insert and heals null transaction ownership during refresh. Conflicting non-null ownership is rejected.

Dashboard request failures display the JSON server message, then the request error message, then the generic fallback. Render startup applies the existing migration chain before launching `wsgi:app` from the backend directory; the planning tables must exist before serving the widget.

## Recurring obligation projection (TP-20261017-001)

`app/services/recurring_obligation_projection.py` (`project_cash_obligations`) is pure and deterministic. `safe_to_spend._obligation_projection` loads owner-verified streams, baseline planned bills, recent posted debits and history coverage, and `_upcoming_bill_payload` remains a `(total, rows)` compatibility wrapper.

- A recurring cash debit due anywhere in `[as_of, protection_end]` reserves cash once, even when it is not due in the display window (Today mode reports `display_window_due_cents: 0` but still reserves it).
- Tiers: `confirmed` streams; `provisional` = detected `proposed` candidate with >= 3 distinct evidence cycles, confidence >= 0.85 and fresh evidence (a temporary reserve that never changes the stored status); `needs_review` rows are informational (`needs_review_cents`, `needs_review_bills`) and are never subtracted.
- Eligibility: own-account transfers, income and card purchases never reserve; a `liability_payment` leaving checking/savings does. Stream accounts must belong to the trusted owner.
- Dedupe: stable key `(account, source id, due date)`; precedence planned bill > confirmed > provisional; a lower-ranked row is dropped only for a shared source id or exactly one same-name/same-amount match within 3 days.
- Paid items: a posted debit within 3 days of an occurrence due on or before `as_of` consumes it.
- Variable detected streams reserve the upper quartile of non-outlier evidence and are flagged `estimated`.
- New response fields: `components.planned_bills_cents`, `confirmed_recurring_cents`, `provisional_recurring_cents`, `needs_review_cents`; `obligation_coverage.warning_codes`, `display_window_due_cents`, `protection_window_reserved_cents`, `alternate_scenarios_ignored`; `upcoming_bills[]` rows `{id,name,account_id,due_date,amount_cents,source,status,estimated,reason_codes}`.
- `confidence` is `ready` only when coverage has no warning (>= 90 days of cash history, owner configured, no stale or unusable plans).
