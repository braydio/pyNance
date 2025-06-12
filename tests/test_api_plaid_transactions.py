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
config_stub.PLAID_CLIENT_ID = "pid"
config_stub.PLAID_CLIENT_NAME = "pname"
config_stub.CLIENT_NAME = "client"
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

env_stub = types.ModuleType("app.config.environment")
sys.modules["app.config.environment"] = env_stub

# SQL stub
sql_pkg = types.ModuleType("app.sql")
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.refresh_data_for_plaid_account = lambda *a, **k: True
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sql_pkg.account_logic = account_logic_stub

# Helpers stub
helpers_pkg = types.ModuleType("app.helpers")
plaid_helpers_stub = types.ModuleType("app.helpers.plaid_helpers")
plaid_helpers_stub.refresh_plaid_categories = lambda *a, **k: None
plaid_helpers_stub.exchange_public_token = lambda *a, **k: None
plaid_helpers_stub.generate_link_token = lambda *a, **k: None
plaid_helpers_stub.get_accounts = lambda *a, **k: []
plaid_helpers_stub.get_institution_name = lambda *a, **k: ""
plaid_helpers_stub.get_item = lambda *a, **k: {}
helpers_pkg.plaid_helpers = plaid_helpers_stub
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.plaid_helpers"] = plaid_helpers_stub

# Models stub
models_stub = types.ModuleType("app.models")


class DummyColumn:
    def __init__(self, attr="val"):
        self.attr = attr

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.attr)

    def __set__(self, instance, value):
        setattr(instance, self.attr, value)

    def in_(self, vals):
        return ("account_id_in", vals)


class DummyPlaidAcct:
    def __init__(self, token):
        self.access_token = token


class DummyAccount:
    account_id = DummyColumn("_account_id")
    user_id = DummyColumn("_user_id")
    plaid_account = None

    def __init__(self, account_id, user_id, name):
        self._account_id = account_id
        self._user_id = user_id
        self.name = name
        self.plaid_account = DummyPlaidAcct(f"t-{account_id}")


class QueryStub:
    def __init__(self, accts):
        self.accts = list(accts)

    def options(self, *a, **k):
        return self

    def filter_by(self, **kw):
        for k, v in kw.items():
            self.accts = [a for a in self.accts if getattr(a, k) == v]
        return self

    def filter(self, cond):
        if isinstance(cond, tuple) and cond[0] == "account_id_in":
            ids = cond[1]
            self.accts = [a for a in self.accts if a.account_id in ids]
        return self

    def all(self):
        return self.accts


models_stub.Account = DummyAccount
models_stub.PlaidAccount = DummyPlaidAcct
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "plaid_transactions.py")
spec = importlib.util.spec_from_file_location(
    "app.routes.plaid_transactions", ROUTE_PATH
)
plaid_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plaid_module)
plaid_module.joinedload = lambda *a, **k: None


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(plaid_module.plaid_transactions, url_prefix="/api/accounts")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_refresh_accounts_filters_and_dates(client, monkeypatch):
    accounts = [
        DummyAccount("a1", "u1", "A1"),
        DummyAccount("a2", "u1", "A2"),
    ]
    plaid_module.Account.query = QueryStub(accounts)

    captured = []

    def fake_refresh(access_token, account_id, start_date=None, end_date=None):
        captured.append((account_id, start_date, end_date))
        return True

    monkeypatch.setattr(
        plaid_module.account_logic, "refresh_data_for_plaid_account", fake_refresh
    )

    resp = client.post(
        "/api/accounts/refresh_accounts",
        json={
            "user_id": "u1",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "account_ids": ["a1"],
        },
    )
    assert resp.status_code == 200
    assert captured and captured[0][0] == "a1"
    assert all(c[0] == "a1" for c in captured)
    assert captured[0][1] == datetime.strptime("2024-01-01", "%Y-%m-%d").date()
    assert captured[0][2] == datetime.strptime("2024-01-31", "%Y-%m-%d").date()
