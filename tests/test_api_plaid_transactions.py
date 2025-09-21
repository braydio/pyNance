"""Test the Plaid transactions route with a stubbed configuration."""

import importlib.util
import os
import sys
import types
from datetime import datetime, timezone

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
config_stub.plaid_client = None
sys.modules["app.config"] = config_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

env_stub = types.ModuleType("app.config.environment")
sys.modules["app.config.environment"] = env_stub

# SQL stub
sql_pkg = types.ModuleType("app.sql")
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.refresh_data_for_plaid_account = lambda *a, **k: (True, None)
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
plaid_helpers_stub.remove_item = lambda *a, **k: None
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

    @staticmethod
    def in_(vals):
        return ("account_id_in", vals)


class DummyPlaidAcct:
    account = None

    def __init__(self, token, account=None):
        self.access_token = token
        self.account = account
        self.account_id = getattr(account, "account_id", None)
        self.last_refreshed = None


class DummyAccount:
    account_id = DummyColumn("_account_id")
    user_id = DummyColumn("_user_id")
    plaid_account = None

    def __init__(self, account_id, user_id, name):
        self._account_id = account_id
        self._user_id = user_id
        self.name = name
        self.balance = 0.0
        self.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
        self.plaid_account = DummyPlaidAcct(f"t-{account_id}", account=self)


class DummyAccountHistory:
    """Mutable stand-in for ``AccountHistory`` rows."""

    def __init__(self, balance: float = 0.0) -> None:
        self.balance = balance
        self.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)


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
models_stub.PlaidItem = type("PlaidItem", (), {})
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
        return True, None

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


def test_delete_account_calls_remove_item(client, monkeypatch):
    called = {}

    monkeypatch.setattr(
        plaid_module, "remove_item", lambda tok: called.setdefault("token", tok)
    )

    plaid_module.PlaidAccount.query = types.SimpleNamespace(
        filter_by=lambda **kw: types.SimpleNamespace(
            first=lambda: types.SimpleNamespace(access_token="tok123")
        )
    )

    plaid_module.Account.query = types.SimpleNamespace(
        filter_by=lambda **kw: types.SimpleNamespace(delete=lambda: 1)
    )

    plaid_module.db = types.SimpleNamespace(
        session=types.SimpleNamespace(commit=lambda: None)
    )

    resp = client.delete("/api/accounts/delete_account", json={"account_id": "acct"})
    assert resp.status_code == 200
    assert called.get("token") == "tok123"


def test_sync_endpoint_updates_balances_and_history(client, monkeypatch):
    """Ensure ``/sync`` updates balances and ``AccountHistory`` entries."""

    account = DummyAccount("acct-123", "user-1", "Main")
    plaid_account = account.plaid_account
    history: list[tuple[str, float]] = []
    history_entry = DummyAccountHistory(balance=account.balance)
    initial_history_updated_at = history_entry.updated_at

    class SessionStub:
        def __init__(self):
            self.commits = 0
            self.rollbacks = 0

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

    session_stub = SessionStub()
    plaid_module.db = types.SimpleNamespace(session=session_stub)

    class Query:
        def __init__(self, record):
            self.record = record

        def options(self, *args, **kwargs):
            return self

        def filter_by(self, **kwargs):
            account_id = kwargs.get("account_id")
            if account_id == self.record.account_id:
                return types.SimpleNamespace(first=lambda: self.record)
            return types.SimpleNamespace(first=lambda: None)

    plaid_module.PlaidAccount.query = Query(plaid_account)

    def fake_refresh(access_token, account_id):
        assert access_token == plaid_account.access_token
        account.balance += 25.0
        history.append((account_id, account.balance))
        history_entry.balance = account.balance
        history_entry.updated_at = datetime.now(timezone.utc)
        return True, None

    monkeypatch.setattr(
        plaid_module.account_logic,
        "refresh_data_for_plaid_account",
        fake_refresh,
    )

    resp = client.post("/api/accounts/sync", json={"account_id": account.account_id})
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload == {
        "status": "success",
        "result": {"updated": True, "error": None},
    }
    assert plaid_account.last_refreshed is not None
    assert account.updated_at > datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert account.balance == 25.0
    assert history == [(account.account_id, 25.0)]
    assert history_entry.balance == 25.0
    assert history_entry.updated_at > initial_history_updated_at
    assert session_stub.commits == 1
    assert session_stub.rollbacks == 0
