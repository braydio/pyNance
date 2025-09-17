"""Tests for dashboard account snapshot routes."""

import importlib.util
import os
import sys
import types

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

app_pkg = types.ModuleType("app")
app_pkg.__path__ = []
sys.modules["app"] = app_pkg

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    error=lambda *a, **k: None,
    info=lambda *a, **k: None,
)
sys.modules["app.config"] = config_stub

services_stub = types.ModuleType("app.services.account_snapshot")
services_stub.DEFAULT_USER_SCOPE = "default"
services_stub.build_snapshot_payload = lambda user_id=None: {}
services_stub.update_snapshot_selection = lambda selected_account_ids, user_id=None: {}
sys.modules["app.services.account_snapshot"] = services_stub


ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "dashboard.py")
spec = importlib.util.spec_from_file_location("app.routes.dashboard", ROUTE_PATH)
dashboard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard_module)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(dashboard_module.dashboard, url_prefix="/api/dashboard")
    with app.test_client() as test_client:
        yield test_client


def test_get_snapshot_success(client, monkeypatch):
    payload = {"selected_account_ids": ["acc-1"], "metadata": {"max_selection": 5}}

    def fake_build(user_id=None):
        assert user_id == "user-123"
        return payload

    monkeypatch.setattr(dashboard_module, "build_snapshot_payload", fake_build)

    resp = client.get("/api/dashboard/account_snapshot?user_id=user-123")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["data"] == payload


def test_put_snapshot_success(client, monkeypatch):
    captured = {}

    def fake_update(selected_account_ids, user_id=None):
        captured["ids"] = selected_account_ids
        captured["user"] = user_id
        return {"selected_account_ids": selected_account_ids}

    monkeypatch.setattr(dashboard_module, "update_snapshot_selection", fake_update)

    resp = client.put(
        "/api/dashboard/account_snapshot?user_id=alpha",
        json={"selected_account_ids": ["a1", "a2"]},
    )
    assert resp.status_code == 200
    assert captured == {"ids": ["a1", "a2"], "user": "alpha"}
    assert resp.get_json()["status"] == "success"


def test_put_snapshot_requires_list(client):
    resp = client.put(
        "/api/dashboard/account_snapshot",
        json={"selected_account_ids": "not-a-list"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["status"] == "error"


def test_put_snapshot_missing_field(client):
    resp = client.put("/api/dashboard/account_snapshot", json={})
    assert resp.status_code == 400
    assert resp.get_json()["status"] == "error"


def test_get_snapshot_handles_error(client, monkeypatch):
    def raise_error(user_id=None):  # pragma: no cover - defensive path
        raise RuntimeError("boom")

    monkeypatch.setattr(dashboard_module, "build_snapshot_payload", raise_error)

    resp = client.get("/api/dashboard/account_snapshot")
    assert resp.status_code == 500
    assert resp.get_json()["status"] == "error"
