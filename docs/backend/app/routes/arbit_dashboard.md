# `arbit_dashboard.py`

Endpoints for the experimental Arbit dashboard.

## Endpoints

- `GET /api/arbit/status` – returns running status and relevant config.
- `GET /api/arbit/metrics` – returns metrics from `arbit_metrics.get_metrics`.
- `GET /api/arbit/opportunities` – placeholder returning `{ "opportunities": [] }` to mirror the production payload.
- `GET /api/arbit/trades` – placeholder returning `{ "trades": [] }` to mirror the production payload.

## Response format

- Metrics responses proxy the exporter output without reshaping the JSON payload.
- Opportunity lookups always return an object with an `opportunities` array.
- Trade lookups always return an object with a `trades` array.
