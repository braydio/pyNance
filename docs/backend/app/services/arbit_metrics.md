# `arbit_metrics.py`

Fetch metrics from the Arbit exporter and parse key values for dashboard use.

## Responsibilities

- Call the configured exporter's `/metrics` endpoint.
- Extract `profit_total`, `orders_total`, `fills_total`, `errors_total`, `skips_total`, and `cycle_latency` from the Prometheus text.
- Return chart-ready series grouped into ``profit`` and ``latency`` arrays, each
  containing ``{"label": str, "value": float}`` mappings for use in the
  frontend charts.

## Usage

```python
from app.services.arbit_metrics import get_metrics

metrics = get_metrics()
# {
#   "profit": [{"label": "Total Profit ($)", "value": 10.0}, ...],
#   "latency": [{"label": "Cycle Latency (s)", "value": 0.8}]
# }
```
