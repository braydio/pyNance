"""Tests for account history routes using stubbed dependencies."""

# pylint: skip-file
# mypy: ignore-errors

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
app_pkg = types.ModuleType("app")
app_pkg.__path__ = []
sys.modules["app"] = app_pkg
sys.modules["flask_cors"] = types.SimpleNamespace(CORS=lambda app: app)
sys.modules["flask_migrate"] = types.SimpleNamespace(Migrate=lambda *a, **k: None)

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FLASK_ENV = "test"
config_stub.plaid_client = None
sys.modules["app.config"] = config_stub

env_stub = types.ModuleType("app.config.environment")
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(session=None)
sys.modules["app.extensions"] = extensions_stub

utils_pkg = types.ModuleType("app.utils")
finance_stub = types.ModuleType("app.utils.finance_utils")
finance_stub.display_transaction_amount = lambda txn: 0.0
finance_stub.normalize_account_balance = lambda b: b
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_stub

models_stub = types.ModuleType("app.models")
models_stub.Account = type("Account", (), {})


class _Col:
    def __init__(self, name):
        self.name = name

    def __ge__(self, other):
        return True

    def __le__(self, other):
        return True

    def __eq__(self, other):
        return True


models_stub.Transaction = type(
    "Transaction",
    (),
    {"date": _Col("date"), "amount": _Col("amount"), "account_id": _Col("account_id")},
)
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
models_stub.PlaidItem = type("PlaidItem", (), {})
models_stub.AccountHistory = type("AccountHistory", (), {})
sys.modules["app.models"] = models_stub

sql_pkg = types.ModuleType("app.sql")
forecast_stub = types.ModuleType("app.sql.forecast_logic")
forecast_stub.update_account_history = lambda *a, **k: None
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.forecast_logic"] = forecast_stub

services_pkg = types.ModuleType("app.services")
history_stub = types.ModuleType("app.services.account_history")
history_stub.compute_balance_history = lambda *a, **k: [
    {"date": "2024-01-01", "balance": 100.0}
]
sys.modules["app.services"] = services_pkg
sys.modules["app.services.account_history"] = history_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "accounts.py")
spec = importlib.util.spec_from_file_location("app.routes.accounts", ROUTE_PATH)
accounts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts_module)


@pytest.fixture
def client(monkeypatch):
    # Stub Account.query to handle account_id or id lookups
    mock_account = types.SimpleNamespace(account_id="acc1", id=1, balance=100.0)

    def filter_by(**kwargs):
        if kwargs.get("account_id") == "acc1":
            return types.SimpleNamespace(first=lambda: mock_account)
        if kwargs.get("id") == 1:
            return types.SimpleNamespace(first=lambda: mock_account)
        return types.SimpleNamespace(first=lambda: None)

    query_obj = types.SimpleNamespace(
        filter_by=filter_by,
        get=lambda pk: mock_account if pk == 1 else None,
    )
    monkeypatch.setattr(
        accounts_module.Account,
        "query",
        query_obj,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "app.models", models_stub)

    # Stub db.session.query chain
    class TxQuery:
        def filter(self, *a, **k):
            return self

        def group_by(self, *a, **k):
            return self

        def all(self):
            return [(date(2024, 1, 1), 0.0)]

    monkeypatch.setattr(
        accounts_module.db,
        "session",
        types.SimpleNamespace(query=lambda *a, **k: TxQuery()),
    )

    # Stub sqlalchemy func
    sqlalchemy_stub = types.SimpleNamespace(
        func=types.SimpleNamespace(date=lambda x: x, sum=lambda x: x)
    )
    monkeypatch.setitem(sys.modules, "sqlalchemy", sqlalchemy_stub)

    app = Flask(__name__)
    app.register_blueprint(accounts_module.accounts, url_prefix="/api/accounts")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_history_accepts_numeric_id(client):
    resp = client.get("/api/accounts/1/history")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["accountId"] == "acc1"
    assert data["balances"][0]["balance"] == 100.0
    assert data["history"] == data["balances"]


def test_history_accepts_account_id(client):
    resp = client.get("/api/accounts/acc1/history")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["accountId"] == "acc1"


def test_history_exact_date_range(client, monkeypatch):
    captured: dict[str, date] = {}

    def fake_compute(balance, txs, start_date, end_date):
        captured["start"] = start_date
        captured["end"] = end_date
        return [{"date": start_date.isoformat(), "balance": 0.0}]

    monkeypatch.setattr(history_stub, "compute_balance_history", fake_compute)
    resp = client.get(
        "/api/accounts/acc1/history?start_date=2024-01-01&end_date=2024-01-05"
    )
    assert resp.status_code == 200
    assert captured["start"] == date(2024, 1, 1)
    assert captured["end"] == date(2024, 1, 5)


def test_history_open_start_date(client, monkeypatch):
    captured: dict[str, date] = {}

    def fake_compute(balance, txs, start_date, end_date):
        captured["start"] = start_date
        captured["end"] = end_date
        return [{"date": start_date.isoformat(), "balance": 0.0}]

    monkeypatch.setattr(history_stub, "compute_balance_history", fake_compute)
    resp = client.get("/api/accounts/acc1/history?start_date=2024-01-01&range=3d")
    assert resp.status_code == 200
    assert captured["start"] == date(2024, 1, 1)
    assert captured["end"] == date(2024, 1, 3)


def test_history_open_end_date(client, monkeypatch):
    captured: dict[str, date] = {}

    def fake_compute(balance, txs, start_date, end_date):
        captured["start"] = start_date
        captured["end"] = end_date
        return [{"date": start_date.isoformat(), "balance": 0.0}]

    monkeypatch.setattr(history_stub, "compute_balance_history", fake_compute)
    resp = client.get("/api/accounts/acc1/history?end_date=2024-01-10&range=3d")
    assert resp.status_code == 200
    assert captured["start"] == date(2024, 1, 8)
    assert captured["end"] == date(2024, 1, 10)


def test_history_empty_results(client, monkeypatch):
    class EmptyTxQuery:
        def filter(self, *a, **k):
            return self

        def group_by(self, *a, **k):
            return self

        def all(self):
            return []

    monkeypatch.setattr(
        accounts_module.db,
        "session",
        types.SimpleNamespace(query=lambda *a, **k: EmptyTxQuery()),
    )
    monkeypatch.setattr(history_stub, "compute_balance_history", lambda *a, **k: [])

    resp = client.get(
        "/api/accounts/acc1/history?start_date=2024-01-01&end_date=2024-01-05"
    )
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["balances"] == []
    assert payload["history"] == []


def test_history_includes_legacy_alias(client):
    resp = client.get("/api/accounts/acc1/history")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert "balances" in payload
    assert "history" in payload
    assert payload["history"] == payload["balances"]


def _patch_account_logic(monkeypatch, delta):
    """Helper to stub ``account_logic.get_net_change`` with ``delta``."""
    account_logic_stub = types.SimpleNamespace(
        get_net_change=lambda aid, s, e: {
            "account_id": aid,
            "net_change": delta,
            "period": {"start": s.isoformat(), "end": e.isoformat()},
        }
    )
    sql_pkg.account_logic = account_logic_stub
    monkeypatch.setitem(sys.modules, "app.sql.account_logic", account_logic_stub)


def test_net_changes_positive_delta(client, monkeypatch):
    _patch_account_logic(monkeypatch, 50.0)
    resp = client.get(
        "/api/accounts/acc1/net_changes?start_date=2024-01-01&end_date=2024-02-01"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["account_id"] == "acc1"
    assert data["net_change"] == 50.0
    assert data["period"] == {"start": "2024-01-01", "end": "2024-02-01"}


def test_net_changes_negative_delta(client, monkeypatch):
    _patch_account_logic(monkeypatch, -25.0)
    resp = client.get(
        "/api/accounts/acc1/net_changes?start_date=2024-01-01&end_date=2024-02-01"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["net_change"] == -25.0
    assert data["period"]["start"] == "2024-01-01"
    assert data["period"]["end"] == "2024-02-01"
