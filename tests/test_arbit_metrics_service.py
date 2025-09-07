"""Tests for the Arbit metrics service."""

import importlib.util
import os

from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
spec = importlib.util.spec_from_file_location(
    "arbit_metrics",
    os.path.join(BASE_BACKEND, "app", "services", "arbit_metrics.py"),
)
arbit_metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbit_metrics)
fetch_metrics = arbit_metrics.fetch_metrics


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:  # pragma: no cover - simple dummy
        pass


def test_fetch_metrics(monkeypatch):
    """`fetch_metrics` returns parsed values from the exporter."""
    sample = """\
# HELP profit_total Total profit
profit_total 1.5
orders_total 10
fills_total 8
errors_total 1
skips_total 2
cycle_latency 0.3
"""

    def mock_get(url: str, timeout: int):
        assert url == "http://exporter/metrics"
        return DummyResponse(sample)

    monkeypatch.setattr(arbit_metrics.requests, "get", mock_get)

    app = Flask(__name__)
    app.config["ARBIT_EXPORTER_URL"] = "http://exporter"

    with app.app_context():
        metrics = fetch_metrics()

    assert metrics == {
        "profit_total": 1.5,
        "orders_total": 10,
        "fills_total": 8,
        "errors_total": 1,
        "skips_total": 2,
        "cycle_latency": 0.3,
    }


def test_get_metrics(monkeypatch):
    """`get_metrics` delegates to `fetch_metrics`."""
    called = {}

    def fake_fetch() -> dict:
        called["used"] = True
        return {"profit_total": 0}

    monkeypatch.setattr(arbit_metrics, "fetch_metrics", fake_fetch)

    assert arbit_metrics.get_metrics() == {"profit_total": 0}
    assert called["used"] is True
