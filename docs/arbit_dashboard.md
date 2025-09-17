# Arbit Dashboard

The Arbit dashboard surfaces exporter metrics and lightweight process controls
for the experimental arbitrage engine. The backend exposes a Flask blueprint at
`/api/arbit`, and the Vue client renders the information in the dashboard view.

## Configuration

- Set `ENABLE_ARBIT_DASHBOARD=true` in `backend/.env` to register the blueprint.
- Configure `ARBIT_EXPORTER_URL` so the backend can reach the Prometheus
  exporter.
- The frontend relies on `VITE_APP_API_BASE_URL` (or the default `/api` proxy)
  to access the dashboard routes.

## HTTP Endpoints

- `GET /api/arbit/status` – reports whether the dashboard is enabled and echoes
  the configured exporter URL.
- `GET /api/arbit/metrics` – returns chart-ready metrics aggregated by
  `app.services.arbit_metrics`.
- `GET /api/arbit/opportunities` – placeholder that currently returns an empty
  list.
- `GET /api/arbit/trades` – placeholder that currently returns an empty list.
- `POST /api/arbit/start` – launch the Arbit CLI with the provided threshold and
  fee.
- `POST /api/arbit/stop` – halt the CLI process.
- `POST /api/arbit/config/update` – update CLI thresholds without restarting.
- `POST /api/arbit/alerts` – evaluate profitability against a user-supplied
  threshold.
- `GET /api/arbit/alerts/stream` – Server-Sent Events stream for alert
  notifications.

## Metrics Payload

The exporter metrics are normalized into chart-friendly series before being
returned to the client. Missing metrics are omitted from the arrays.

```
GET /api/arbit/metrics

{
  "profit": [
    { "label": "Total Profit ($)", "value": 12.5 },
    { "label": "Net Profit (%)", "value": 3.2 },
    { "label": "Orders", "value": 4.0 },
    { "label": "Fills", "value": 3.0 },
    { "label": "Errors", "value": 1.0 },
    { "label": "Skips", "value": 2.0 }
  ],
  "latency": [
    { "label": "Cycle Latency (s)", "value": 0.8 }
  ]
}
```

`frontend/src/components/ArbitMetrics.vue` consumes the response and renders the
series through `PortfolioAllocationChart.vue`.

## UI

Visit `/arbit` in the frontend to access the dashboard. The view displays
status, charts for the metrics above, opportunity placeholders, and alert
notifications.
