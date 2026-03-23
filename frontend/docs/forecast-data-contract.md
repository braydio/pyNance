# Forecast chart data contract

The forecast UI now reads typed aspect series directly from `POST /api/forecast/compute`.

## Response field

The API exposes a top-level `series` object keyed by stable aspect identifiers:

- `realized_income`
- `manual_adjustments`
- `spending`
- `debt_totals`

Each entry includes:

- `id`: stable backend/frontend identifier
- `label`: user-facing chart label
- `points`: ordered daily points with `date`, `label`, and `value`
- `metadata`: optional diagnostics and rendering hints

## Frontend usage

- `useForecastData.ts` stores the typed `series` payload alongside the legacy `timeline`, `cashflows`, and `summary` fields.
- `ForecastLayout.vue` uses `series.manual_adjustments` and `series.realized_income` for the sidebar summaries.
- `ForecastChart.vue` renders the selected aspect directly from the matching backend series instead of rebuilding aspect datasets from generic `cashflows` rows.

## Compatibility

The API still returns `timeline`, `cashflows`, and `summary` so existing consumers remain compatible during migration.
