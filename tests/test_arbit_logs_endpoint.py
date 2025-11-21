"""Tests for the RSAssistant log feed endpoint."""

import importlib.util
import os
import sys
import types
from pathlib import Path

from flask import Flask

# Ensure configuration imports succeed during tests
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///test.db")

BASE_BACKEND = Path(__file__).resolve().parents[1] / "backend"
SPEC = importlib.util.spec_from_file_location(
    "arbit_dashboard",
    BASE_BACKEND / "app" / "routes" / "arbit_dashboard.py",
)

# Stub the ``app`` package so the route module can import without full app setup.
stub_app = types.ModuleType("app")
stub_services = types.ModuleType("app.services")
stub_services.arbit_cli = types.SimpleNamespace(start=None, stop=None, update_config=None)
stub_services.arbit_metrics = types.SimpleNamespace(
    get_metrics=lambda: {}, check_profit_alert=lambda threshold: {"alert": False, "threshold": threshold}
)
stub_config = types.ModuleType("app.config")
stub_constants = types.ModuleType("app.config.constants")
stub_constants.RS_ASSISTANT_LOG_FILE = Path("rsassistant.log")
sys.modules.update(
    {
        "app": stub_app,
        "app.services": stub_services,
        "app.config": stub_config,
        "app.config.constants": stub_constants,
    }
)

arbit_dashboard = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(arbit_dashboard)


def _make_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(arbit_dashboard.arbit_dashboard, url_prefix="/api/arbit")
    app.config["TESTING"] = True
    return app


def test_recent_log_lines_are_returned(tmp_path, monkeypatch):
    """Only the newest lines up to the requested limit are returned."""

    log_file = tmp_path / "rsassistant.log"
    log_file.write_text("one\ntwo\nthree\n", encoding="utf-8")
    monkeypatch.setattr(arbit_dashboard, "RS_ASSISTANT_LOG_FILE", log_file)

    client = _make_app().test_client()
    response = client.get("/api/arbit/logs?limit=2")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["lines"] == ["two", "three"]
    assert payload["limit"] == 2
    assert payload["last_updated"]


def test_invalid_limits_are_clamped(monkeypatch, tmp_path):
    """Non-numeric or excessive limits fall back to safe defaults."""

    log_file = tmp_path / "rsassistant.log"
    lines = [str(i) for i in range(600)]
    log_file.write_text("\n".join(lines), encoding="utf-8")
    monkeypatch.setattr(arbit_dashboard, "RS_ASSISTANT_LOG_FILE", log_file)

    client = _make_app().test_client()
    response = client.get("/api/arbit/logs?limit=999")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["lines"]) == 500
    assert payload["lines"][-1] == "599"

    invalid_response = client.get("/api/arbit/logs?limit=abc")
    invalid_payload = invalid_response.get_json()
    assert invalid_payload["limit"] == 50
