# Safe to Spend Dashboard Widget

_Last updated: 2026-07-12_

## Purpose

The Safe to Spend widget gives the dashboard an immediate daily decision surface: how much can be spent now while preserving a protected cash buffer and known near-term obligations.

## Dashboard placement

The widget lives in `frontend/src/components/dashboard/SafeToSpendCard.vue` and is composed by `NetOverviewSection` beside the account snapshot and Daily Net chart. This keeps it in the dashboard's current-position area rather than the retrospective category breakdown or lower drill-down tables.

## API contract

`GET /api/dashboard/safe-to-spend`

Query params:

- `mode`: `today`, `until_payday`, or `week`; unknown values fall back to `today`.
- `as_of`: optional `YYYY-MM-DD` date. Defaults to the backend's current date.
- `buffer_cents`: optional protected buffer in integer cents. Defaults to `$250.00`.
- `user_id`: optional account/transaction scope.

Response shape:

```json
{
  "status": "success",
  "data": {
    "amount_cents": 4200,
    "total_horizon_cents": 4200,
    "per_day_cents": 4200,
    "status": "caution",
    "currency": "USD",
    "mode": "today",
    "as_of": "2026-07-12",
    "horizon_end": "2026-07-12",
    "next_income_date": null,
    "confidence": "ready",
    "components": {
      "spendable_cash_cents": 124000,
      "upcoming_outflows_cents": 86000,
      "required_buffer_cents": 25000,
      "spent_today_cents": 8800
    },
    "accounts": [],
    "upcoming_bills": [],
    "message": "You have about $42 today."
  }
}
```

## Decision math

The backend computes a horizon-level spend amount as:

```text
spendable cash - upcoming planned bills - protected buffer - spent today
```

The result is clamped to zero. `today` displays the whole clamped amount. `until_payday` and `week` display a per-day amount while preserving `total_horizon_cents` for drill-down copy.

## Feature-complete next version

The first implementation already includes the horizon controls planned for the next version:

- Today
- Until Payday
- This Week

Follow-up work should add user-editable buffer settings, richer bill-source attribution, and a drill-down detail drawer for included accounts, upcoming bills, today's transactions, and payday inference.
