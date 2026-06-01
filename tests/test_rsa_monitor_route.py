"""Tests for the RSA monitor API route."""

from __future__ import annotations

import importlib.util
import os
import sys
import types

from flask import Flask

ROUTE_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "routes", "rsa_monitor.py")


def _load_route_module(monkeypatch):
    config_stub = types.ModuleType("app.config")
    config_stub.logger = types.SimpleNamespace(error=lambda *a, **k: None)
    service_stub = types.ModuleType("app.services.rsa_monitor")
    service_stub.build_rsa_monitor_status = lambda: {"overall_status": "ok", "components": []}
    monkeypatch.setitem(sys.modules, "app.config", config_stub)
    monkeypatch.setitem(sys.modules, "app.services.rsa_monitor", service_stub)

    spec = importlib.util.spec_from_file_location("app.routes.rsa_monitor", ROUTE_PATH)
    route_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(route_module)
    return route_module


def test_rsa_monitor_status_route_returns_payload(monkeypatch):
    route_module = _load_route_module(monkeypatch)
    app = Flask(__name__)
    app.register_blueprint(route_module.rsa_monitor, url_prefix="/api/rsa-monitor")

    response = app.test_client().get("/api/rsa-monitor/status")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["data"]["overall_status"] == "ok"
