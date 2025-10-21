# `summary.py`

Aggregate financial metrics powering the summary dashboard widgets. Blueprint is
registered at `/api/summary`.

## Endpoint

| Method | Path                     | Description                                                                                          |
| ------ | ------------------------ | ---------------------------------------------------------------------------------------------------- |
| `GET`  | `/api/summary/financial` | Computes income, expenses, net totals, trend, volatility, and outlier dates for the requested range. |

## Query Parameters

- `start_date` (optional) – ISO `YYYY-MM-DD`. Defaults to 30 days before today.
- `end_date` (optional) – ISO `YYYY-MM-DD`. Defaults to today.

## Implementation Notes

- Joins `Transaction` and `Account` via SQLAlchemy to exclude hidden accounts and
  internal transfers.
- Uses SQL `CASE` expressions (`sqlalchemy.case`) to split income vs. expense
  values before aggregating totals.
- Performs lightweight analytics (average day counts, simple regression trend,
  volatility calculation, and outlier detection) in Python.
- Returns `{ "status": "success", "data": { ... } }` with rounded totals, or an
  empty metrics payload if no transactions match the filter.
- Exceptions bubble up as `{ "status": "error", "message": <details> }` with a
  500 response code.
