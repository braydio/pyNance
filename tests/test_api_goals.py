"""Tests for goals API routes."""

import importlib.util
import os
import sys
import types
from datetime import date

import pytest
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
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(
    session=types.SimpleNamespace(add=lambda x: None, commit=lambda: None)
)
sys.modules["app.extensions"] = extensions_stub

models_stub = types.ModuleType("app.models")


class DummyGoal:
    def __init__(self, **kwargs):
        self.id = 1
        for k, v in kwargs.items():
            setattr(self, k, v)


models_stub.FinancialGoal = DummyGoal
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "goals.py")
spec = importlib.util.spec_from_file_location("app.routes.goals", ROUTE_PATH)
goals_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(goals_module)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(goals_module.goals, url_prefix="/api/goals")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_list_goals_returns_data(client, monkeypatch):
    sample = DummyGoal(
        user_id="u1",
        account_id="a1",
        name="Pay card",
        target_amount=100.0,
        due_date=date(2025, 1, 1),
        notes=None,
    )
    monkeypatch.setattr(
        goals_module.FinancialGoal,
        "query",
        types.SimpleNamespace(all=lambda: [sample]),
        raising=False,
    )
    resp = client.get("/api/goals")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["data"][0]["name"] == "Pay card"


def test_create_goal_returns_id(client, monkeypatch):
    added = []
    monkeypatch.setattr(
        goals_module.db,
        "session",
        types.SimpleNamespace(add=lambda obj: added.append(obj), commit=lambda: None),
    )
    resp = client.post(
        "/api/goals",
        json={
            "user_id": "u1",
            "account_id": "a1",
            "name": "Pay card",
            "target_amount": 50,
            "due_date": "2025-01-01",
        },
    )
    assert resp.status_code == 201
    assert len(added) == 1
    assert resp.get_json()["id"] == 1
