"""Tests for transaction-related API routes."""

import importlib.util
import os
import sys
import types

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# Config stub
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FILES = {}
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

# SQL package and logic
sql_pkg = types.ModuleType("app.sql")
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.get_paginated_transactions = lambda *a, **k: ([{"id": "t1"}], 1)
transaction_rules_logic_stub = types.ModuleType("app.sql.transaction_rules_logic")
transaction_rules_logic_stub.create_rule = lambda *a, **k: None
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sys.modules["app.sql.transaction_rules_logic"] = transaction_rules_logic_stub
sql_pkg.account_logic = account_logic_stub
sql_pkg.transaction_rules_logic = transaction_rules_logic_stub

models_stub = types.ModuleType("app.models")
models_stub.Account = type("Account", (), {})
models_stub.Transaction = type("Transaction", (), {})
models_stub.AccountHistory = type("AccountHistory", (), {})
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "transactions.py")
spec = importlib.util.spec_from_file_location("app.routes.transactions", ROUTE_PATH)
transactions_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transactions_module)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(
        transactions_module.transactions, url_prefix="/api/transactions"
    )
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_transactions_returns_data(client, monkeypatch):
    monkeypatch.setattr(
        transactions_module.account_logic,
        "get_paginated_transactions",
        lambda *a, **k: ([{"txn": 1}], 1),
    )
    resp = client.get("/api/transactions/get_transactions")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["data"]["transactions"] == [{"txn": 1}]
    assert data["data"]["total"] == 1


def test_account_transactions_recent_limited_and_sorted(client, monkeypatch):
    """Verify recent transactions are limited and sorted by date."""
    sample = [
        {"transaction_id": "t1", "date": "2024-02-01"},
        {"transaction_id": "t2", "date": "2024-01-15"},
        {"transaction_id": "t3", "date": "2024-01-01"},
    ]
    captured = {}

    def fake_get_paginated(
        page,
        page_size,
        start_date=None,
        end_date=None,
        category=None,
        user_id=None,
        account_id=None,
        recent=False,
        limit=None,
    ):
        captured["recent"] = recent
        captured["limit"] = limit
        ordered = sorted(sample, key=lambda x: x["date"], reverse=True)
        return ordered[: (limit or page_size)], len(sample)

    monkeypatch.setattr(
        transactions_module.account_logic,
        "get_paginated_transactions",
        fake_get_paginated,
    )
    resp = client.get("/api/transactions/acc1/transactions?recent=true&limit=2")
    assert resp.status_code == 200
    data = resp.get_json()
    ids = [t["transaction_id"] for t in data["data"]["transactions"]]
    assert ids == ["t1", "t2"]
    assert len(ids) == 2
    assert captured["recent"] is True
    assert captured["limit"] == 2
