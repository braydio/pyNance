---
Owner: Backend Team
Last Updated: 2026-07-12
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
- Non-internal negative `Transaction` records on the as-of date for today's spending.
- Recent income-like transactions to infer a likely next payday.

## Edge cases

- Unknown modes fall back to `today`.
- Missing account data yields `confidence: limited` or `estimated` rather than failing the dashboard.
- Negative spend room is clamped to zero and reported as `do_not_spend`.
