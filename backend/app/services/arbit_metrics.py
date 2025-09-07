"""Retrieve and parse metrics from the Arbit exporter."""

from __future__ import annotations

from typing import Dict

import requests
from flask import current_app

METRIC_NAMES = (
    "profit_total",
    "orders_total",
    "fills_total",
    "errors_total",
    "skips_total",
    "cycle_latency",
)


def fetch_metrics() -> Dict[str, float | int]:
    """Fetch the `/metrics` endpoint and parse select values.

    Returns:
        Mapping of metric names to numeric values.
    """
    base_url: str = current_app.config["ARBIT_EXPORTER_URL"]
    response = requests.get(f"{base_url}/metrics", timeout=5)
    response.raise_for_status()
    return parse_metrics(response.text)


def parse_metrics(prom_text: str) -> Dict[str, float | int]:
    """Parse Prometheus metrics text into a dictionary.

    Args:
        prom_text: Raw text from a Prometheus metrics endpoint.

    Returns:
        JSON-serializable mapping containing the selected metric values.
        Missing metrics default to 0.
    """
    metrics: Dict[str, float | int] = {name: 0 for name in METRIC_NAMES}

    for line in prom_text.splitlines():
        if line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        name, value = parts
        if name not in metrics:
            continue
        if name in {"profit_total", "cycle_latency"}:
            metrics[name] = float(value)
        else:
            metrics[name] = int(float(value))

    return metrics
