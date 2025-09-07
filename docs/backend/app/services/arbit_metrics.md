# `arbit_metrics.py`

Fetch metrics from the Arbit exporter and parse key values for dashboard use.

## Responsibilities

- Call the configured exporter's `/metrics` endpoint.
- Extract `profit_total`, `orders_total`, `fills_total`, `errors_total`, `skips_total`, and `cycle_latency` from the Prometheus text.
- Return a JSON-ready dictionary of these metrics.

## Usage

```python
from app.services.arbit_metrics import get_metrics

metrics = get_metrics()
```
