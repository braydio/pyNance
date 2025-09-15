"""Tests for planning API endpoints using FastAPI.

This module stubs minimal application components to exercise the
planning logic via HTTP requests. It verifies that bills can be added
to a scenario and that percent allocation caps are enforced.
"""
# pylint: disable=import-error,too-few-public-methods,redefined-outer-name

import importlib.util
import os
import sys
import types
import uuid
from datetime import date

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from werkzeug.exceptions import BadRequest

# ---------------------------------------------------------------------------
# Module stubs so planning_logic can be imported without the full app.
# ---------------------------------------------------------------------------
BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)
app_pkg = types.ModuleType("app")
app_pkg.__path__ = []
sys.modules["app"] = app_pkg

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(  # type: ignore[attr-defined]
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
sys.modules["app.config"] = config_stub
sys.modules["app.config.environment"] = types.ModuleType("app.config.environment")

# In-memory storage for scenarios
scenarios: dict[uuid.UUID, "PlanningScenario"] = {}


class Session:
    """Minimal DB session stub that stores scenarios in-memory."""

    def add(self, obj) -> None:
        """Store the object if it exposes an ``id`` attribute."""
        if getattr(obj, "id", None):
            scenarios[obj.id] = obj

    def commit(self) -> None:
        """No-op commit to satisfy the interface."""

    def delete(self, obj) -> None:
        """Remove the object from in-memory storage."""
        scenarios.pop(obj.id, None)


db_stub = types.SimpleNamespace(session=Session())
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = db_stub  # type: ignore[attr-defined]
sys.modules["app.extensions"] = extensions_stub


class Query:
    """Simplistic query helper for fetching scenarios by ID."""

    def filter_by(self, **kwargs):
        """Return an object with a ``first`` method yielding a scenario."""
        scenario_id = kwargs.get("id")
        return types.SimpleNamespace(first=lambda: scenarios.get(scenario_id))


class PlanningScenario:
    """In-memory representation of a planning scenario."""

    query = Query()

    def __init__(self, name: str):
        """Initialize a scenario with no bills or allocations."""
        self.id = uuid.uuid4()
        self.name = name
        self.bills: list[PlannedBill] = []  # type: ignore[name-defined]
        self.allocations: list[ScenarioAllocation] = []  # type: ignore[name-defined]
        self.created_at = date.today()


class PlannedBill:
    """Simple bill record used by tests."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        amount_cents: int,
        due_date: date | None,
        category: str | None = None,
        predicted: bool = False,
    ) -> None:
        """Store provided bill metadata."""
        self.id = uuid.uuid4()
        self.name = name
        self.amount_cents = amount_cents
        self.due_date = due_date
        self.category = category
        self.predicted = predicted


class ScenarioAllocation:
    """In-memory allocation record."""

    def __init__(self, target: str, kind: str, value: int) -> None:
        """Store allocation target and amount."""
        self.id = uuid.uuid4()
        self.target = target
        self.kind = kind
        self.value = value


models_stub = types.ModuleType("app.models")
models_stub.PlanningScenario = PlanningScenario  # type: ignore[attr-defined]
models_stub.PlannedBill = PlannedBill  # type: ignore[attr-defined]
models_stub.ScenarioAllocation = ScenarioAllocation  # type: ignore[attr-defined]
sys.modules["app.models"] = models_stub

# Import planning_logic with stubs in place
spec = importlib.util.spec_from_file_location(
    "app.sql.planning_logic",
    os.path.join(BASE_BACKEND, "app", "sql", "planning_logic.py"),
)
planning_logic = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec and spec.loader  # nosec
spec.loader.exec_module(planning_logic)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# FastAPI application exposing planning endpoints.
# ---------------------------------------------------------------------------
app = FastAPI()


@app.post("/api/planning", status_code=201)
def create_scenario(payload: dict):
    """Create a new scenario with the provided name."""

    try:
        scenario = planning_logic.create_scenario(payload.get("name", ""))
    except BadRequest as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": str(scenario.id), "name": scenario.name}


@app.put("/api/planning/{scenario_id}")
def update_scenario(scenario_id: uuid.UUID, payload: dict):
    """Replace a scenario's bills and allocations."""

    try:
        updated = planning_logic.update_scenario(scenario_id, payload)
    except BadRequest as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": str(updated.id), "ok": True}


@app.get("/api/planning/{scenario_id}")
def get_scenario(scenario_id: uuid.UUID):
    """Retrieve a scenario by ID."""

    scenario = planning_logic.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "bills": [
            {
                "id": str(b.id),
                "name": b.name,
                "amount_cents": b.amount_cents,
                "due_date": b.due_date.isoformat() if b.due_date else None,
                "category": b.category,
                "predicted": b.predicted,
            }
            for b in scenario.bills
        ],
        "allocations": [
            {"id": str(a.id), "target": a.target, "kind": a.kind, "value": a.value}
            for a in scenario.allocations
        ],
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def api_client():
    """Yield a TestClient for the FastAPI planning app."""

    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_state():
    """Ensure each test starts with a clean in-memory store."""

    scenarios.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_bill_creation_flow(api_client: TestClient):
    """Bills added via update endpoint should be returned by get."""

    resp = api_client.post("/api/planning", json={"name": "My Plan"})
    assert resp.status_code == 201  # nosec
    scenario_id = resp.json()["id"]

    resp = api_client.put(
        f"/api/planning/{scenario_id}",
        json={
            "bills": [
                {
                    "name": "Rent",
                    "amount_cents": 10000,
                    "due_date": "2024-01-01",
                    "category": "housing",
                    "predicted": False,
                }
            ]
        },
    )
    assert resp.status_code == 200  # nosec

    resp = api_client.get(f"/api/planning/{scenario_id}")
    assert resp.status_code == 200  # nosec
    data = resp.json()
    assert data["bills"][0]["name"] == "Rent"  # nosec
    assert data["bills"][0]["amount_cents"] == 10000  # nosec


def test_allocation_percent_cap_enforced(api_client: TestClient):
    """Percent allocations exceeding 100 should return HTTP 400."""

    scenario_id = api_client.post("/api/planning", json={"name": "Cap Plan"}).json()[
        "id"
    ]

    resp = api_client.put(
        f"/api/planning/{scenario_id}",
        json={
            "allocations": [
                {"target": "savings", "kind": "percent", "value": 60},
                {"target": "invest", "kind": "percent", "value": 50},
            ]
        },
    )
    assert resp.status_code == 400  # nosec
