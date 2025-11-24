# Arbit Dashboard Routes (`arbit_dashboard.py`)

## Purpose
Expose experimental endpoints for the Arbit dashboard, surfacing exporter metrics alongside placeholder payloads that mirror production shapes.

## Endpoints
- `GET /api/arbit/status` – Return running status and configuration flags.
- `GET /api/arbit/metrics` – Proxy metrics from `arbit_metrics.get_metrics`.
- `GET /api/arbit/opportunities` – Provide an opportunities payload (currently placeholder).
- `GET /api/arbit/trades` – Provide a trades payload (currently placeholder).

## Inputs/Outputs
- **GET endpoints**
  - **Inputs:** None; all routes are queryless reads.
  - **Outputs:**
    - Status returns a config/status object.
    - Metrics proxy the exporter JSON without reshaping.
    - Opportunities responses always include an `opportunities` array.
    - Trades responses always include a `trades` array.

## Auth
- Intended for internal diagnostics; relies on the standard application auth controls when enabled by feature flags.

## Dependencies
- `arbit_metrics.get_metrics` for live exporter data.
- App configuration toggles controlling whether the blueprint is registered.

## Behaviors/Edge Cases
- When no data is available, opportunities and trades still return empty arrays to preserve response shape.
- Metrics errors bubble from the exporter; callers should handle unavailable metrics.

## Sample Request/Response
```http
GET /api/arbit/metrics HTTP/1.1
```

```json
{
  "metrics": {
    "latency_ms": 120,
    "throughput": 42
  }
}
```
