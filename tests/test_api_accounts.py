import importlib.util
import os
import sys
import types
from types import SimpleNamespace

import pytest
from flask import Flask

# Base setup
BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# Mocks and stubs
captured = []


def fake_plaid(token, account_id, start_date=None, end_date=None):
    captured.append(("plaid", account_id, start_date, end_date))
    return True


# --- Config stub ---
config_stub = types.ModuleType("app.config")
config_stub.logger = SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FILES = {"TELLER_DOT_CERT": "cert", "TELLER_DOT_KEY": "key"}
config_stub.TELLER_API_BASE_URL = "https://example.com"
config_stub.FLASK_ENV = "test"
config_stub.plaid_client = SimpleNamespace(
    Accounts=SimpleNamespace(get=lambda *a, **k: {"accounts": []})
)
sys.modules["app.config"] = config_stub

# --- Extensions stub ---
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = SimpleNamespace(commit=lambda: None, rollback=lambda: None)
sys.modules["app.extensions"] = extensions_stub

# --- Helpers stub ---
helpers_pkg = types.ModuleType("app.helpers")
teller_helpers_stub = types.ModuleType("app.helpers.teller_helpers")
teller_helpers_stub.load_tokens = lambda: [{"user_id": "u1", "access_token": "tok"}]
helpers_pkg.teller_helpers = teller_helpers_stub
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.teller_helpers"] = teller_helpers_stub

# --- SQL package and logic stub ---
sql_pkg = types.ModuleType("app.sql")
sql_pkg.__path__ = []  # Mark as package
account_logic_stub = types.ModuleType("app.sql.account_logic")
forecast_logic_stub = types.ModuleType("app.sql.forecast_logic")
account_logic_stub.refresh_data_for_plaid_account = fake_plaid
forecast_logic_stub.update_account_history = lambda *a, **k: True
sql_pkg.account_logic = account_logic_stub
sql_pkg.forecast_logic = forecast_logic_stub
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sys.modules["app.sql.forecast_logic"] = forecast_logic_stub

# --- Models stub ---
models_stub = types.ModuleType("app.models")


class DummyColumn:
    def __init__(self, attr="val"):
        self.attr = attr

    def __get__(self, instance, owner):
        return getattr(instance, self.attr)

    def __set__(self, instance, value):
        setattr(instance, self.attr, value)

    def in_(self, vals):
        return ("account_id_in", vals)


class DummyAccount:
    account_id = DummyColumn("_account_id")
    user_id = DummyColumn("_user_id")

    def __init__(self, account_id, user_id, link_type):
        self._account_id = account_id
        self._user_id = user_id
        self.link_type = link_type
        self.plaid_account = (
            SimpleNamespace(access_token="token") if link_type == "Plaid" else None
        )
        self.teller_account = None


models_stub.Account = DummyAccount
models_stub.RecurringTransaction = type("RT", (), {})
sys.modules["app.models"] = models_stub

# --- Load route module ---
ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "accounts.py")
spec = importlib.util.spec_from_file_location("app.routes.accounts", ROUTE_PATH)
accounts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts_module)


# --- Client fixture ---
@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(accounts_module.accounts, url_prefix="/api/accounts")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# --- Sample test ---
def test_refresh_all_accounts_simple(client):
    accounts_module.Account.query = SimpleNamespace(
        all=lambda: [DummyAccount("a1", "u1", "Plaid")]
    )
    resp = client.post(
        "/api/accounts/refresh_accounts",
        json={
            "account_ids": ["a1"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )
    assert resp.status_code == 200
