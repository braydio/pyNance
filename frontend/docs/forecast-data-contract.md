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

## V2 (liquid-cash) responses

When the request sets `model_version: "v2"`, the response adds `model_version`, `liquidity`, `net_worth`,
`uncertainty`, `drivers`, `data_quality` and `scenarios` (full contract in
`docs/backend/app/routes/forecast.md`). `forecast_balance` and `liquid_cash` are liquid cash only. Timeline points carry
`p10`/`p50`/`p90` only when `uncertainty.available` is true.

- `useForecastData.ts` sends the V2 request (`simulation`, up to 5 `scenarios`), maps the new fields, aborts the
  previous request and ignores stale responses (latest request wins). It defaults to `v1` when `modelVersion` is not
  supplied. Server error messages (for example a 403) are surfaced as the error text.
- `ForecastSummaryPanel.vue` leads with cash today, cash at the end, lowest cash and any projected shortfall, then the
  simulated risk (or why it is unavailable). Debt, investments and net worth appear only as a separate note.
- `ForecastChart.vue` draws the P10-P90 band, the P50 line and scenario overlays when present.
- `ForecastBreakdown.vue` lists scheduled events (with origin and confidence) and data-quality warnings under
  "What drives this forecast"; `ForecastScenarioComparison.vue` compares replayed scenarios against the baseline.
- `ForecastLayout.vue` requests V2 by default; set `VITE_FORECAST_MODEL_VERSION=v1` to roll back, or use the model
  selector under Advanced model controls.

