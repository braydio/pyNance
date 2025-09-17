# `arbit_dashboard.py`

Endpoints for the experimental Arbit dashboard.

## Endpoints

- `GET /api/arbit/status` – returns running status and relevant config.
- `GET /api/arbit/metrics` – returns chart-ready metrics with `profit` and
  `latency` arrays of `{"label": str, "value": float}` objects sourced from
  `arbit_metrics.get_metrics`.
- `GET /api/arbit/opportunities` – placeholder returning an empty list.
- `GET /api/arbit/trades` – placeholder returning an empty list.
