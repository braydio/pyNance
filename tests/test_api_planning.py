"""API tests for SQL-backed Planning routes."""

from __future__ import annotations

import os
import sys

from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
os.environ.setdefault("PLAID_CLIENT_ID", "sandbox-client")
os.environ.setdefault("PLAID_SECRET_KEY", "sandbox-secret")
os.environ.setdefault("CLIENT_NAME", "pyNance Test Suite")
os.environ.setdefault("BACKEND_PUBLIC_URL", "http://localhost")

for module_name in list(sys.modules):
    if not (
        module_name in {"app.config", "app.models", "app.services"}
        or module_name.startswith("app.config.")
    ):
        continue
    existing = sys.modules.get(module_name)
    if existing is not None and getattr(existing, "__file__", None) is None:
        sys.modules.pop(module_name, None)

app_module = sys.modules.get("app")
if app_module is not None and getattr(app_module, "__file__", None) is None:
    sys.modules.pop("app", None)

from app.extensions import db
from app.routes.planning import planning


def _build_client():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    app.register_blueprint(planning, url_prefix="/api/planning")

    with app.app_context():
        db.create_all()

    return app.test_client(), app


def test_planning_bill_crud_persists_to_database():
    client, app = _build_client()

    scenario_response = client.post(
        "/api/planning/scenarios",
        json={
            "name": "April plan",
            "accountId": "checking-1",
            "planningBalanceCents": 250000,
            "currencyCode": "USD",
        },
    )
    assert scenario_response.status_code == 201
    scenario = scenario_response.get_json()

    create_response = client.post(
        "/api/planning/bills",
        json={
            "name": "Rent",
            "amountCents": 125000,
            "dueDate": "2026-05-01",
            "frequency": "monthly",
            "category": "Housing",
            "origin": "manual",
            "accountId": "checking-1",
            "scenarioId": scenario["id"],
        },
    )
    assert create_response.status_code == 201
    bill = create_response.get_json()
    assert bill["amountCents"] == 125000
    assert bill["scenarioId"] == scenario["id"]

    update_response = client.put(
        f"/api/planning/bills/{bill['id']}",
        json={"amountCents": 130000, "category": "Rent"},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["amountCents"] == 130000

    list_response = client.get("/api/planning/bills")
    assert list_response.status_code == 200
    assert [row["name"] for row in list_response.get_json()] == ["Rent"]

    delete_response = client.delete(f"/api/planning/bills/{bill['id']}")
    assert delete_response.status_code == 200

    with app.app_context():
        assert client.get("/api/planning/bills").get_json() == []


def test_planning_rejects_invalid_bill_payloads():
    client, _app = _build_client()
    scenario = client.post("/api/planning/scenarios", json={"name": "Baseline"}).get_json()

    response = client.post(
        "/api/planning/bills",
        json={
            "name": "",
            "amountCents": -1,
            "frequency": "monthly",
            "origin": "manual",
            "scenarioId": scenario["id"],
        },
    )

    assert response.status_code == 400


def test_scenario_allocation_routes_enforce_percent_cap():
    client, _app = _build_client()
    scenario = client.post("/api/planning/scenarios", json={"name": "Baseline"}).get_json()

    response = client.put(
        f"/api/planning/scenarios/{scenario['id']}/allocations",
        json=[
            {"target": "Savings", "kind": "percent", "value": 60},
            {"target": "Debt", "kind": "percent", "value": 50},
        ],
    )
    assert response.status_code == 400

    ok_response = client.put(
        f"/api/planning/scenarios/{scenario['id']}/allocations",
        json=[
            {"target": "Savings", "kind": "percent", "value": 40},
            {"target": "Rent", "kind": "fixed", "value": 125000},
        ],
    )
    assert ok_response.status_code == 200
    allocations = ok_response.get_json()
    assert [allocation["target"] for allocation in allocations] == ["Savings", "Rent"]

    list_response = client.get(f"/api/planning/scenarios/{scenario['id']}/allocations")
    assert list_response.status_code == 200
    assert len(list_response.get_json()) == 2
