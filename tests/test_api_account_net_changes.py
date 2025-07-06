"""Tests for the account net changes endpoint."""

import importlib.util
import os
import sys
import types
from datetime import datetime

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
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

# Environment stub
env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

# Extensions stub
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

# SQL stub
sql_pkg = types.ModuleType("app.sql")
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.get_net_changes = lambda *a, **k: None
forecast_logic_stub = types.ModuleType("app.sql.forecast_logic")
forecast_logic_stub.update_account_history = lambda *a, **k: None
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sys.modules["app.sql.forecast_logic"] = forecast_logic_stub
sql_pkg.account_logic = account_logic_stub

# Utils stub
utils_pkg = types.ModuleType("app.utils")
finance_utils_stub = types.ModuleType("app.utils.finance_utils")
finance_utils_stub.normalize_account_balance = lambda bal, typ: bal
utils_pkg.finance_utils = finance_utils_stub
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_utils_stub

# Models stub
models_stub = types.ModuleType("app.models")
models_stub.Account = type("Account", (), {})
models_stub.Transaction = type("Transaction", (), {})
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "accounts.py")
spec = importlib.util.spec_from_file_location("app.routes.accounts", ROUTE_PATH)
accounts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts_module)
accounts_module.account_logic = account_logic_stub


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(accounts_module.accounts, url_prefix="/api/accounts")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_net_changes_no_dates(client, monkeypatch):
    captured = {}

    def fake_get_net_changes(account_id, start_date=None, end_date=None):
        captured["args"] = (account_id, start_date, end_date)
        return {"income": 100, "expense": -50, "net": 50}

    monkeypatch.setattr(
        accounts_module.account_logic, "get_net_changes", fake_get_net_changes
    )
    resp = client.get("/api/accounts/acc1/net_changes")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["data"] == {"income": 100, "expense": -50, "net": 50}
    assert captured["args"] == ("acc1", None, None)


def test_net_changes_with_dates(client, monkeypatch):
    captured = {}

    def fake_get_net_changes(account_id, start_date=None, end_date=None):
        captured["args"] = (account_id, start_date, end_date)
        return {"income": 100, "expense": -20, "net": 80}

    monkeypatch.setattr(
        accounts_module.account_logic, "get_net_changes", fake_get_net_changes
    )
    resp = client.get(
        "/api/accounts/acc1/net_changes?start_date=2024-01-01&end_date=2024-02-01"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["data"] == {"income": 100, "expense": -20, "net": 80}
    assert captured["args"][0] == "acc1"
    assert captured["args"][1] == datetime.strptime("2024-01-01", "%Y-%m-%d").date()
    assert captured["args"][2] == datetime.strptime("2024-02-01", "%Y-%m-%d").date()
