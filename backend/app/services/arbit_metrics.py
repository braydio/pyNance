"""Retrieve and parse metrics from the Arbit exporter."""

from __future__ import annotations

from typing import Dict, Tuple, TypedDict

import requests
from flask import current_app

SERIES_CONFIG: Dict[str, Tuple[Tuple[str, str], ...]] = {
    "profit": (
        ("Total Profit ($)", "profit_total"),
        ("Net Profit (%)", "net_profit_percent"),
        ("Orders", "orders_total"),
        ("Fills", "fills_total"),
        ("Errors", "errors_total"),
        ("Skips", "skips_total"),
    ),
    "latency": (("Cycle Latency (s)", "cycle_latency"),),
}

METRIC_NAMES = tuple(
    metric for series in SERIES_CONFIG.values() for _, metric in series
)


class MetricPoint(TypedDict):
    """Typed mapping describing a chart data point."""

    label: str
    value: float


def fetch_metrics() -> Dict[str, float | int]:
    """Fetch the `/metrics` endpoint and parse select values.

    Returns:
        Mapping of metric names to numeric values.
    """
    base_url: str = current_app.config["ARBIT_EXPORTER_URL"]
    response = requests.get(f"{base_url}/metrics", timeout=5)
    response.raise_for_status()
    return parse_metrics(response.text)


def get_metrics() -> Dict[str, list[MetricPoint]]:
    """Retrieve exporter metrics formatted for chart consumption."""

    raw_metrics = fetch_metrics()
    return _format_chart_metrics(raw_metrics)


def parse_metrics(prom_text: str) -> Dict[str, float | int]:
    """Parse Prometheus metrics text into a dictionary.

    Args:
        prom_text: Raw text from a Prometheus metrics endpoint.

    Returns:
        JSON-serializable mapping containing the selected metric values.
        Missing metrics default to ``0``.
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
        if name in {"profit_total", "cycle_latency", "net_profit_percent"}:
            metrics[name] = float(value)
        else:
            metrics[name] = int(float(value))

    return metrics


def _format_chart_metrics(raw: Dict[str, float | int]) -> Dict[str, list[MetricPoint]]:
    """Convert raw exporter metrics into chart-friendly series using ``SERIES_CONFIG``."""

    formatted: Dict[str, list[MetricPoint]] = {}

    for series_name, fields in SERIES_CONFIG.items():
        points: list[MetricPoint] = []
        for label, key in fields:
            value = raw.get(key)
            if value is None:
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            points.append({"label": label, "value": numeric})
        formatted[series_name] = points

    return formatted


def check_profit_alert(threshold: float) -> Dict[str, float | bool]:
    """Evaluate whether ``net_profit_percent`` exceeds ``threshold``.

    Args:
        threshold: Percent threshold to trigger an alert.

    Returns:
        Mapping with ``net_profit_percent`` and whether an ``alert`` was
        triggered.
    """
    metrics = fetch_metrics()
    net_profit = float(metrics.get("net_profit_percent", 0))
    return {
        "net_profit_percent": net_profit,
        "alert": net_profit > threshold,
        "threshold": threshold,
    }
