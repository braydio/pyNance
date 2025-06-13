import importlib.util
import os
import sys
import types
from datetime import datetime
from types import SimpleNamespace

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
config_stub.FILES = {"TELLER_DOT_CERT": "cert", "TELLER_DOT_KEY": "key"}
config_stub.TELLER_API_BASE_URL = "https://example.com"
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

# Extensions stub
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(commit=lambda: None, rollback=lambda: None)
sys.modules["app.extensions"] = extensions_stub

# Helpers stub
helpers_pkg = types.ModuleType("app.helpers")
teller_helpers_stub = types.ModuleType("app.helpers.teller_helpers")
teller_helpers_stub.load_tokens = lambda: [{"user_id": "u1", "access_token": "tok"}]
helpers_pkg.teller_helpers = teller_helpers_stub
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.teller_helpers"] = teller_helpers_stub

# SQL stub
sql_pkg = types.ModuleType("app.sql")
account_logic_stub = types.ModuleType("app.sql.account_logic")

captured = []


def fake_plaid(token, account_id, start_date=None, end_date=None):
    captured.append(("plaid", account_id, start_date, end_date))
    return True


def fake_teller(account, token, cert, key, base_url, start_date=None, end_date=None):
    captured.append(("teller", account.account_id, start_date, end_date))
    return True


account_logic_stub.refresh_data_for_plaid_account = fake_plaid
account_logic_stub.refresh_data_for_teller_account = fake_teller
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sql_pkg.account_logic = account_logic_stub

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


class DummyPlaid:
    def __init__(self, token):
        self.access_token = token
        self.last_refreshed = None


class DummyTeller:
    def __init__(self, token):
        self.access_token = token
        self.last_refreshed = None


class DummyAccount:
    account_id = DummyColumn("_account_id")
    user_id = DummyColumn("_user_id")

    def __init__(
        self,
        account_id,
        user_id,
        link_type,
        plaid_account=None,
        teller_account=None,
    ):
        self._account_id = account_id
        self._user_id = user_id
        self.link_type = link_type
        self.plaid_account = plaid_account or (
            DummyPlaid("p") if link_type == "Plaid" else None
        )
        self.teller_account = teller_account or (
            DummyTeller("t") if link_type == "Teller" else None
        )


class QueryStub:
    def __init__(self, accts):
        self.accts = list(accts)

    def filter(self, cond):
        if isinstance(cond, tuple) and cond[0] == "account_id_in":
            ids = cond[1]
            self.accts = [a for a in self.accts if a.account_id in ids]
        return self

    def all(self):
        return self.accts


models_stub.Account = DummyAccount
models_stub.RecurringTransaction = type("RT", (), {})
sys.modules["app.models"] = models_stub

# Load the real blueprint module from backend
ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "accounts.py")
spec = importlib.util.spec_from_file_location("app.routes.accounts", ROUTE_PATH)
accounts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts_module)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(accounts_module.accounts, url_prefix="/api/accounts")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_refresh_all_accounts_filters_and_dates(client):
    accounts = [
        DummyAccount(
            account_id="a1",
            user_id="u1",
            link_type="Plaid",
            plaid_account=SimpleNamespace(access_token="plaid-token-123"),
        ),
        DummyAccount(
            account_id="a2",
            user_id="u1",
            link_type="Teller",
            teller_account=SimpleNamespace(access_token="teller-token-456"),
        ),
    ]

    accounts_module.Account.query = QueryStub(accounts)
    captured.clear()

    resp = client.post(
        "/api/accounts/refresh_accounts",
        json={
            "account_ids": ["a1"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )
    assert resp.status_code == 200
