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
- `PlannedBill` records in the selected horizon.
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
