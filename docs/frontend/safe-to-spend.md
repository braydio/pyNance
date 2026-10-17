# Safe to Spend Dashboard Widget

_Last updated: 2026-10-17_

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
- `user_id`: optional; the owner is always the server-configured `PYNANCE_OWNER_USER_ID` (503 if unset, 403 if different).

Response shape:

```json
{
  "status": "success",
  "data": {
    "amount_cents": 2307,
    "daily_allowance_cents": 2307,
    "total_protected_room_cents": 30000,
    "total_horizon_cents": 30000,
    "per_day_cents": 2307,
    "calculation_version": "2",
    "display_window": { "start": "2026-10-17", "end": "2026-10-17", "days": 1 },
    "protection_window": { "start": "2026-10-17", "end": "2026-10-29", "days": 13, "basis": "day_before_payday", "payday_verified": true },
    "warnings": [],
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

## Decision math (calculation_version 2)

```text
total_protected_room = max(0, usable cash - bills through protection_end - protected buffer)
daily_allowance      = floor(total_protected_room / protection days)
```

- `amount_cents`, `daily_allowance_cents` and `per_day_cents` are the **daily allowance**, identical in every mode for the same evidence (switching Today, Next 7 Days or Until Payday never inflates it).
- `total_horizon_cents` and `total_protected_room_cents` are all discretionary cash through `protection_end` (a secondary figure, never called today's allowance). `display_window_allowance_cents` is the allowance times the display days.
- Usable cash comes from `cash_coverage` / `opening_cash_sources` (see TP-20261017-006); spent-today is shown but never deducted, because balances already include it.

Windows (inclusive, rolling, from `as_of`):

| Mode | `display_window` | `protection_window` |
| --- | --- | --- |
| Today | today | through the day before the validated payday, else the 14-day fallback (today..today+13) |
| Next 7 Days | today..today+6 | the longer of its own 7 days and the Today protection |
| Until Payday | through `protection_end` | same as Today |

A payday that is today but not yet posted (`awaiting_payday_post`) is never counted as cash and falls back to the 14-day window. `horizon_end` is kept for compatibility and equals `protection_window.end`.

`status` is tightness (`do_not_spend`, `tight`, `caution`, `comfortable`). `confidence` is evidence completeness (`limited`, `estimated`, `ready`) and is `ready` only when `warnings` is empty: cash availability and age are verified, the payday is confirmed, and recurring obligations are projected (`obligation_coverage.complete`, set by TP-20261017-001). The default `$250` buffer is disclosed in the card and in `default_buffer_cents`. Historical dashboard ranges (3M/YTD) never affect this decision.

## Horizon controls

- Today
- Until Payday
- Next 7 Days (a rolling 7-day window, not the calendar week)

Follow-up work should add user-editable buffer settings and a drill-down detail drawer (TP-20261017-002).

## Reliability and transaction ownership

Spending uses positive Plaid amounts and negative non-Plaid amounts; income candidates use negative Plaid amounts and positive non-Plaid amounts, followed by the income metadata check. Stored transaction signs remain unchanged. Both transaction queries scope through `Account.user_id`, including transactions whose own `user_id` is null.

The legacy Plaid refresh delegates to the shared upsert, which writes account ownership on insert and heals null transaction ownership during refresh. Conflicting non-null ownership is rejected.

Dashboard request failures display the JSON server message, then the request error message, then the generic fallback. Render startup applies the existing migration chain before launching `wsgi:app` from the backend directory; the planning tables must exist before serving the widget.
