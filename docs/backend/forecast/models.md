---
Owner: Backend Team
Last Updated: 2026-04-08
Status: Active
---

# Forecast Response Models

## Purpose

`backend/forecast/models.py` defines typed, JSON-serializable models for the forecast API payload. The
module provides structured objects for timeline charting, cashflow breakdowns, adjustments, aspect-
specific chart series, and summary metrics so the frontend can render forecast insights consistently.

## Models

### `ForecastTimelinePoint`

Represents a point on the forecast timeline, including the label and projected/actual balances. Use
this for chart series and balance deltas.

### `ForecastCashflowItem`

Captures a single cashflow line item that drives the projection. Each item includes the date, amount,
category, source, optional type/confidence annotations, and optional account identifiers for
breakdown widgets. Items may now also include optional `sources` references (transactions/events)
when attribution can be derived from recurring rules, category averages, or adjustments.

### `ForecastSeriesPoint`

Represents a single daily point in a named aspect series. These points are designed for frontend
chart overlays and summary widgets that should not infer meaning from generic cashflow rows.

### `ForecastAspectSeries`

Encapsulates a named daily series with a stable `id`, user-facing `label`, and ordered `points`.
The forecast compute response currently emits aspect series for realized income used by the
auto-calculation baseline, manual user adjustments, spending totals, and debt totals.

### `ForecastAdjustment`

Represents manual or automated adjustments applied to the projection (e.g., overrides or one-off
changes). These are surfaced in adjustment UI panels for transparency and auditing.

### `ForecastSummary`

Aggregates top-line forecast metrics such as starting/ending balances, inflows/outflows, and category
breakdowns. This powers summary tiles and headline statistics in the dashboard, including the
depletion date when balances reach zero or below.

### `ForecastResult`

Encapsulates the full response payload for the forecast endpoint. Use `ForecastResult.to_dict()` to
produce the JSON payload with `timeline`, `summary`, `cashflows`, `adjustments`, and a typed `series`
object. Existing consumers can continue to read the legacy fields while newer clients use `series`
for aspect-specific chart data keyed by stable backend identifiers.

## Usage Notes

- All models are import-safe with no side effects.
- Dates accept ISO strings, `date`, or `datetime` instances and serialize to ISO strings.
- Decimal values are normalized to floats during serialization for JSON compatibility.
- `ForecastResult.series` serializes a dedicated `ForecastSeriesCollection`, which guarantees the
  top-level `series` object uses the supported aspect keys (`realized_income`, `manual_adjustments`,
  `spending`, and `debt_totals`).
