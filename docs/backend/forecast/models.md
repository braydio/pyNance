---
Owner: Backend Team
Last Updated: 2026-01-25
Status: Active
---

# Forecast Response Models

## Purpose

`backend/forecast/models.py` defines typed, JSON-serializable models for the forecast API payload. The
module provides structured objects for timeline charting, cashflow breakdowns, adjustments, and
summary metrics so the frontend can render forecast insights consistently.

## Models

### `ForecastTimelinePoint`

Represents a point on the forecast timeline, including the label and projected/actual balances. Use
this for chart series and balance deltas.

### `ForecastCashflowItem`

Captures a single cashflow line item that drives the projection. Each item includes the date, amount,
category, source, optional type/confidence annotations, and optional account identifiers for
breakdown widgets.

### `ForecastAdjustment`

Represents manual or automated adjustments applied to the projection (e.g., overrides or one-off
changes). These are surfaced in adjustment UI panels for transparency and auditing.

### `ForecastSummary`

Aggregates top-line forecast metrics such as starting/ending balances, inflows/outflows, and category
breakdowns. This powers summary tiles and headline statistics in the dashboard, including the
depletion date when balances reach zero or below.

### `ForecastResult`

Encapsulates the full response payload for the forecast endpoint. Use `ForecastResult.to_dict()` to
produce the JSON payload with `timeline`, `summary`, `cashflows`, and `adjustments` keys.

## Usage Notes

- All models are import-safe with no side effects.
- Dates accept ISO strings, `date`, or `datetime` instances and serialize to ISO strings.
- Decimal values are normalized to floats during serialization for JSON compatibility.
