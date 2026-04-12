"""Tests for dashboard activity-status route behavior."""

import importlib.util
import os
import sys
import types

from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
sys.modules["app.config"] = config_stub

services_pkg = types.ModuleType("app.services")
sys.modules["app.services"] = services_pkg

account_groups_stub = types.ModuleType("app.services.account_groups")
account_groups_stub.DEFAULT_USER_SCOPE = "default-user"
sys.modules["app.services.account_groups"] = account_groups_stub
services_pkg.account_groups = account_groups_stub

account_snapshot_stub = types.ModuleType("app.services.account_snapshot")
account_snapshot_stub.build_snapshot_payload = lambda user_id=None: {"user_id": user_id, "accounts": []}
account_snapshot_stub.update_snapshot_selection = lambda selected_ids, user_id=None: {
    "selected_account_ids": selected_ids,
    "user_id": user_id,
}
sys.modules["app.services.account_snapshot"] = account_snapshot_stub

activity_stub = types.ModuleType("app.services.dashboard_activity_status")
activity_stub.generate_activity_status = lambda **_: {
    "status_key": "largest_expense",
    "message": "Review your largest recent expense for accuracy.",
    "source": "fallback",
}
sys.modules["app.services.dashboard_activity_status"] = activity_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "dashboard.py")
spec = importlib.util.spec_from_file_location("app.routes.dashboard", ROUTE_PATH)
dashboard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard_module)


def _build_client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(dashboard_module.dashboard, url_prefix="/api/dashboard")
    return app.test_client()


def test_activity_status_validates_date_format():
    client = _build_client()
    response = client.get("/api/dashboard/activity-status?start_date=04-01-2026")
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_activity_status_returns_parseable_payload():
    client = _build_client()
    response = client.get("/api/dashboard/activity-status?start_date=2026-04-01&end_date=2026-04-08")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["data"]["status_key"] == "largest_expense"
    assert "message" in payload["data"]
