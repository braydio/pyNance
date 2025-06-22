import importlib.util
import os
import sys
import types
from types import SimpleNamespace

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# -------------------------
# Shared Stubs and Mocks
# -------------------------

# app.config (package)
config_pkg = types.ModuleType("app.config")
config_pkg.__path__ = []
config_pkg.logger = SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
sys.modules["app.config"] = config_pkg
sys.modules["app.config"].FILES = config_pkg.FILES

# app.config.environment
env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "stub"
sys.modules["app.config.environment"] = env_stub

# app.config.plaid_config
plaid_stub = types.ModuleType("app.config.plaid_config")
plaid_stub.plaid_client = SimpleNamespace(
    Accounts=SimpleNamespace(get=lambda *a, **kw: {"accounts": []})
)
sys.modules["app.config.plaid_config"] = plaid_stub

# app.extensions
ext_stub = types.ModuleType("app.extensions")
ext_stub.db = SimpleNamespace(commit=lambda: None, rollback=lambda: None)
sys.modules["app.extensions"] = ext_stub

# app.models
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


class DummyAccount:
    account_id = DummyColumn("_account_id")
    user_id = DummyColumn("_user_id")

    def __init__(
        self, account_id, user_id, link_type, plaid_account=None, teller_account=None
    ):
        self._account_id = account_id
        self._user_id = user_id
        self.link_type = link_type
        self.plaid_account = plaid_account
        self.teller_account = teller_account


DummyRT = type("RecurringTransaction", (), {})
models_stub.Account = DummyAccount
models_stub.RecurringTransaction = DummyRT
sys.modules["app.models"] = models_stub

# app.sql as package with account_logic and forecast_logic
sql_pkg = types.ModuleType("app.sql")
sql_pkg.__path__ = []
sys.modules["app.sql"] = sql_pkg

account_logic_stub = types.ModuleType("app.sql.account_logic")
forecast_logic_stub = types.ModuleType("app.sql.forecast_logic")


def fake_plaid(token, account_id, start_date=None, end_date=None):
    return True


account_logic_stub.refresh_data_for_plaid_account = fake_plaid
forecast_logic_stub.update_account_history = lambda *args, **kwargs: True

sys.modules["app.sql.account_logic"] = account_logic_stub
sys.modules["app.sql.forecast_logic"] = forecast_logic_stub

# app.utils
utils_pkg = types.ModuleType("app.utils")
finance_utils_stub = types.ModuleType("app.utils.finance_utils")
finance_utils_stub.normalize_account_balance = lambda acct: acct
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_utils_stub

# -------------------------
# Load Blueprint
# -------------------------

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


def test_refresh_accounts_sanity(client):
    resp = client.post("/api/accounts/refresh_accounts", json={})
    print("\n=== DEBUG (refresh_accounts_sanity) ===")
    print("Status code:", resp.status_code)
    print("Response data:", resp.get_data(as_text=True))
    print("=======================================")
    assert resp.status_code in {200, 400}, f"Got 500: {resp.get_data(as_text=True)}"
