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

The blueprint currently exposes the routes below. Unless otherwise noted, all
responses are JSON encoded and use HTTP 200 on success.

### `GET /api/arbit/status`

Returns whether the dashboard is enabled and echoes the relevant configuration.

```json
{
  "running": true,
  "config": {
    "arbit_exporter_url": "http://localhost:9876",
    "enable_arbit_dashboard": true
  }
}
```

### `GET /api/arbit/metrics`

Retrieves chart-ready series derived from the exporter. Each series contains a
`label` and numeric `value` for the profit and latency groups that
`frontend/src/components/ArbitMetrics.vue` can render directly.

```json
{
  "profit": [
    { "label": "Total Profit ($)", "value": 12.5 },
    { "label": "Net Profit (%)", "value": 3.2 },
    { "label": "Orders", "value": 4 },
    { "label": "Fills", "value": 3 },
    { "label": "Errors", "value": 1 },
    { "label": "Skips", "value": 2 }
  ],
  "latency": [{ "label": "Cycle Latency (s)", "value": 0.8 }]
}
```

### `GET /api/arbit/opportunities`

Placeholder that currently returns an empty list. Reserved for surfaced trade
candidates.

### `GET /api/arbit/trades`

Placeholder returning an empty list for completed trade history.

### `POST /api/arbit/start`

Launches the CLI worker with the supplied configuration. The request **must**
include both `threshold` (profit percent trigger, must be greater than zero)
and `fee` (expected fees, zero or greater).

```bash
curl -X POST /api/arbit/start \
  -H 'Content-Type: application/json' \
  -d '{"threshold": 2.5, "fee": 0.15}'
```

Successful responses include the captured CLI output:

```json
{
  "stdout": "...",
  "stderr": "...",
  "returncode": 0
}
```

### `POST /api/arbit/stop`

Stops the running CLI process. No request body is required. The response mirrors
`/start` by returning `stdout`, `stderr`, and the `returncode` produced by the
shutdown command.

### `POST /api/arbit/config/update`

Hot-reloads CLI parameters without restarting the worker. Supply the same JSON
payload as `/start`:

```json
{ "threshold": 2.5, "fee": 0.15 }
```

### `POST /api/arbit/alerts`

Evaluates the most recent exporter metrics against a provided profit threshold.
The request body must include a numeric `threshold` property. If the
`net_profit_percent` exceeds that value, the response marks `"alert": true` and
queues the event for the stream described below.

### `GET /api/arbit/alerts/stream`

Server-Sent Events (SSE) feed that broadcasts alert payloads as soon as they are
produced. Clients should subscribe with `EventSource` (or an equivalent SSE
library) and expect messages shaped like:

```json
{
  "net_profit_percent": 3.7,
  "alert": true,
  "threshold": 2.5
}
```

The stream remains open until the client disconnects. Remember to close the
connection when unmounting UI components to prevent resource leaks.

## Frontend View

`frontend/src/views/ArbitDashboard.vue` currently renders the `ArbitAlerts`
component, which listens to the `/api/arbit/alerts/stream` SSE endpoint via the
browser's `EventSource` API. Operators must ensure the blueprint is enabled and
that the frontend's API base URL correctly proxies `/api/arbit` so the component
can establish the stream.
