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
        "app.services.arbit_cli",
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
    sample = {
        "profit": [{"label": "Total Profit ($)", "value": 1.0}],
        "latency": [{"label": "Cycle Latency (s)", "value": 0.5}],
    }
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


def test_start_endpoint(monkeypatch):
    """`/start` validates input and runs the CLI."""
    app = make_app(True)
    called: dict[str, list[str]] = {}

    def fake_run(cmd, capture_output, text, check):
        called["cmd"] = cmd

        class Res:
            stdout = "started"
            stderr = ""
            returncode = 0

        return Res()

    monkeypatch.setattr("app.services.arbit_cli.subprocess.run", fake_run)
    client = app.test_client()
    resp = client.post("/api/arbit/start", json={"threshold": 1, "fee": 0.1})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["stdout"] == "started"
    assert called["cmd"] == [
        "python",
        "arbit/cli.py",
        "start",
        "--threshold",
        "1.0",
        "--fee",
        "0.1",
    ]


def test_start_invalid_payload():
    """Missing or invalid fields return 400."""
    app = make_app(True)
    client = app.test_client()
    resp = client.post("/api/arbit/start", json={"threshold": "x", "fee": 0.1})
    assert resp.status_code == 400


def test_stop_endpoint(monkeypatch):
    """`/stop` executes the CLI."""
    app = make_app(True)

    def fake_run(cmd, capture_output, text, check):
        assert cmd == ["python", "arbit/cli.py", "stop"]

        class Res:
            stdout = "stopped"
            stderr = ""
            returncode = 0

        return Res()

    monkeypatch.setattr("app.services.arbit_cli.subprocess.run", fake_run)
    client = app.test_client()
    resp = client.post("/api/arbit/stop")
    assert resp.status_code == 200
    assert resp.get_json()["stdout"] == "stopped"


def test_config_update_endpoint(monkeypatch):
    """`/config/update` runs the CLI with validated values."""
    app = make_app(True)
    called: dict[str, list[str]] = {}

    def fake_run(cmd, capture_output, text, check):
        called["cmd"] = cmd

        class Res:
            stdout = "updated"
            stderr = ""
            returncode = 0

        return Res()

    monkeypatch.setattr("app.services.arbit_cli.subprocess.run", fake_run)
    client = app.test_client()
    resp = client.post("/api/arbit/config/update", json={"threshold": 2, "fee": 0.2})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["stdout"] == "updated"
    assert called["cmd"] == [
        "python",
        "arbit/cli.py",
        "config",
        "update",
        "--threshold",
        "2.0",
        "--fee",
        "0.2",
    ]


def test_config_update_invalid():
    """Invalid numbers yield a 400 response."""
    app = make_app(True)
    client = app.test_client()
    resp = client.post("/api/arbit/config/update", json={"threshold": -1, "fee": 0.2})
    assert resp.status_code == 400


def test_alert_endpoint(monkeypatch):
    """`/alerts` evaluates metrics and returns the result."""
    app = make_app(True)
    called = {}

    def fake_check(threshold):
        called["threshold"] = threshold
        return {"alert": True, "net_profit_percent": 6, "threshold": threshold}

    monkeypatch.setattr(
        "app.routes.arbit_dashboard.arbit_metrics.check_profit_alert", fake_check
    )
    client = app.test_client()
    resp = client.post("/api/arbit/alerts", json={"threshold": 5})
    assert resp.status_code == 200
    assert resp.get_json()["alert"] is True
    assert called["threshold"] == 5
