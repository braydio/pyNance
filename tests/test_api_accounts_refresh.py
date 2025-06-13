import importlib.util
import os
import sys
import types
from types import SimpleNamespace

import pytest
from flask import Flask

# --- Setup path ---
BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)
app_pkg = types.ModuleType("app")
sys.modules["app"] = app_pkg

# --- app.config stub ---
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
sys.modules["app.config"] = config_stub

# --- app.extensions stub ---
extensions_stub = types.ModuleType("app.extensions")
session_ns = types.SimpleNamespace(commit=lambda: None, rollback=lambda: None)
extensions_stub.db = types.SimpleNamespace(
    session=session_ns, commit=lambda: None, rollback=lambda: None
)
sys.modules["app.extensions"] = extensions_stub

# --- app.helpers stub ---
helpers_pkg = types.ModuleType("app.helpers")
teller_helpers_stub = types.ModuleType("app.helpers.teller_helpers")
teller_helpers_stub.load_tokens = lambda: [{"user_id": "u1", "access_token": "tok"}]
helpers_pkg.teller_helpers = teller_helpers_stub
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.teller_helpers"] = teller_helpers_stub

utils_pkg = types.ModuleType("app.utils")
finance_utils_stub = types.ModuleType("app.utils.finance_utils")
finance_utils_stub.normalize_account_balance = lambda balance, t: balance
utils_pkg.finance_utils = finance_utils_stub
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_utils_stub

# SQL stub
sql_pkg = types.ModuleType("app.sql")
sql_pkg.__path__ = []

account_logic_stub = types.ModuleType("app.sql.account_logic")
forecast_logic_stub = types.ModuleType("app.sql.forecast_logic")

forecast_logic_stub.update_account_history = lambda *a, **k: None

captured = []


def fake_plaid(token, account_id, start_date=None, end_date=None):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    captured.append(("plaid", account_id, start_date, end_date))
    return True


def fake_teller(account, token, cert, key, base_url, start_date=None, end_date=None):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    captured.append(("teller", account.account_id, start_date, end_date))
    return True


account_logic_stub.refresh_data_for_plaid_account = fake_plaid
account_logic_stub.refresh_data_for_teller_account = fake_teller
forecast_logic_stub.update_account_history = lambda *a, **kw: True

sql_pkg.account_logic = account_logic_stub
sql_pkg.forecast_logic = forecast_logic_stub

sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sys.modules["app.sql.forecast_logic"] = forecast_logic_stub
sql_pkg.account_logic = account_logic_stub

# --- Models stub ---
models_stub = types.ModuleType("app.models")


class DummyColumn:
    def __init__(self, attr="val"):
        self.attr = attr

    def __get__(self, instance, owner):
        return getattr(instance, self.attr) if instance else self

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

    def __init__(self, aid, uid, link_type, institution_name="Bank"):
        self._account_id = aid
        self._user_id = uid
        self.link_type = link_type
        self.institution_name = institution_name
        self.name = aid
        self.plaid_account = DummyPlaid("p") if link_type == "Plaid" else None
        self.teller_account = DummyTeller("t") if link_type == "Teller" else None


class QueryStub:
    def __init__(self, accts):
        self.accts = list(accts)

    def filter(self, cond):
        if isinstance(cond, tuple) and cond[0] == "account_id_in":
            self.accts = [a for a in self.accts if a.account_id in cond[1]]
        return self

    def all(self):
        return self.accts


models_stub.Account = DummyAccount
models_stub.RecurringTransaction = type("RT", (), {})
sys.modules["app.models"] = models_stub

# --- Load blueprint ---
ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "accounts.py")
spec = importlib.util.spec_from_file_location("app.routes.accounts", ROUTE_PATH)
accounts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts_module)


# --- Flask test client fixture ---
@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(accounts_module.accounts, url_prefix="/api/accounts")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# --- Test case ---
def test_refresh_all_accounts_filters_and_dates(client):
    accounts = [
        DummyAccount("a1", "u1", "Plaid", "Bank A"),
        DummyAccount("a2", "u1", "Teller", "Bank A"),
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
    assert captured == [
        ("plaid", "a1", datetime(2024, 1, 1).date(), datetime(2024, 1, 31).date())
    ]
    data = resp.get_json()
    assert data["refreshed_counts"] == {"Bank A": 1}
