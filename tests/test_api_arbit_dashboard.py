"""Tests for the `/api/arbit` dashboard routes."""

from __future__ import annotations

import os
import sys

from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)


def make_app(flag: bool) -> Flask:
    """Create a Flask app with the arbit dashboard optionally registered."""
    for mod in [
        "app.routes.arbit_dashboard",
        "app.services",
        "app.services.arbit_metrics",
    ]:
        sys.modules.pop(mod, None)
    from app.routes import arbit_dashboard as arbit_module

    app = Flask(__name__)
    app.config["ENABLE_ARBIT_DASHBOARD"] = flag
    app.config["ARBIT_EXPORTER_URL"] = "http://localhost:8000"
    if flag:
        app.register_blueprint(arbit_module.arbit_dashboard, url_prefix="/api/arbit")
    return app


def test_endpoints_disabled():
    """Endpoints return 404 when the dashboard is disabled."""
    app = make_app(False)
    client = app.test_client()
    for path in (
        "/api/arbit/status",
        "/api/arbit/metrics",
        "/api/arbit/opportunities",
        "/api/arbit/trades",
    ):
        assert client.get(path).status_code == 404


def test_status_enabled():
    """`/status` reports running state and config when enabled."""
    app = make_app(True)
    client = app.test_client()
    resp = client.get("/api/arbit/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["running"] is True
    assert data["config"]["enable_arbit_dashboard"] is True


def test_metrics_endpoint(monkeypatch):
    """`/metrics` proxies results from `arbit_metrics.get_metrics`."""
    app = make_app(True)
    sample = {"profit_total": 1}
    monkeypatch.setattr(
        "app.routes.arbit_dashboard.arbit_metrics.get_metrics", lambda: sample
    )
    with app.test_client() as client:
        resp = client.get("/api/arbit/metrics")
        assert resp.status_code == 200
        assert resp.get_json() == sample


def test_stub_endpoints():
    """`/opportunities` and `/trades` return empty lists."""
    app = make_app(True)
    client = app.test_client()
    resp = client.get("/api/arbit/opportunities")
    assert resp.status_code == 200
    assert resp.get_json() == []
    resp = client.get("/api/arbit/trades")
    assert resp.status_code == 200
    assert resp.get_json() == []
