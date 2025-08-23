"""Tests for the transaction update endpoint."""

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

# Config stub with silent logger
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
sys.modules["app.config"] = config_stub

# Extensions stub
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(
    session=types.SimpleNamespace(commit=lambda: None)
)
sys.modules["app.extensions"] = extensions_stub

# Stub transaction object and query
_txn = types.SimpleNamespace(
    transaction_id="t1",
    amount=0,
    date=None,
    description="",
    category="",
    merchant_name="",
    merchant_type="",
    is_internal=False,
    internal_match_id=None,
    user_modified=False,
    user_modified_fields=None,
    user_id=1,
    category_id=None,
)


def _filter_by(transaction_id):
    class _Result:
        def first(self_inner):
            return _txn if transaction_id == _txn.transaction_id else None

    return _Result()


models_stub = types.ModuleType("app.models")
models_stub.Transaction = types.SimpleNamespace(
    query=types.SimpleNamespace(filter_by=_filter_by)
)
models_stub.Account = type("Account", (), {})
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


def test_update_transaction_valid_date(client):
    resp = client.put(
        "/api/transactions/update",
        json={"transaction_id": "t1", "date": "2024-01-02"},
    )
    assert resp.status_code == 200
    assert _txn.date == date(2024, 1, 2)


def test_update_transaction_invalid_date(client):
    resp = client.put(
        "/api/transactions/update",
        json={"transaction_id": "t1", "date": "bad"},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "error"
