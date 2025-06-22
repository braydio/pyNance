import sys
import types
import os
import importlib.util
from types import SimpleNamespace
import pytest
from flask import Flask

# -------------------------
# Setup: Patch sys.modules for app + config stubs
# -------------------------
BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# Patch 'app' as package
sys.modules["app"] = types.ModuleType("app")
sys.modules["app"].__path__ = []

# Patch 'app.config' as package with FILES at top-level (matches app/config/__init__.py)
config_pkg = types.ModuleType("app.config")
config_pkg.__path__ = []
config_pkg.FILES = {
    "TELLER_DOT_CERT": "dummy_cert",
    "TELLER_DOT_KEY": "dummy_key",
    "TELLER_TOKENS": "dummy_tokens.json",
    # Add any additional keys your code might expect!
}
config_pkg.TELLER_API_BASE_URL = "https://example.com"
config_pkg.FLASK_ENV = "test"
config_pkg.logger = SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
sys.modules["app.config"] = config_pkg

# (If you ever do from app.config.constants import FILES, also add this:)
constants_stub = types.ModuleType("app.config.constants")
constants_stub.FILES = config_pkg.FILES
sys.modules["app.config.constants"] = constants_stub

# app.extensions stub
ext_stub = types.ModuleType("app.extensions")
ext_stub.db = SimpleNamespace(commit=lambda: None, rollback=lambda: None)
sys.modules["app.extensions"] = ext_stub

# app.models stub
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
        self,
        account_id,
        user_id,
        link_type,
        institution_name="Bank",
        plaid_account=None,
        teller_account=None,
    ):
        self._account_id = account_id
        self._user_id = user_id
        self.link_type = link_type
        self.institution_name = institution_name
        self.plaid_account = plaid_account
        self.teller_account = teller_account


models_stub.Account = DummyAccount
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
sys.modules["app.models"] = models_stub

# app.sql/account_logic stub (needed for blueprint import)
sql_pkg = types.ModuleType("app.sql")
sql_pkg.__path__ = []
sys.modules["app.sql"] = sql_pkg
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.refresh_data_for_plaid_account = lambda *a, **k: True
sys.modules["app.sql.account_logic"] = account_logic_stub

# app.sql.forecast_logic stub
forecast_logic_stub = types.ModuleType("app.sql.forecast_logic")
forecast_logic_stub.update_account_history = lambda *a, **k: True
sys.modules["app.sql.forecast_logic"] = forecast_logic_stub

# app.utils/finance_utils stub
utils_pkg = types.ModuleType("app.utils")
finance_utils_stub = types.ModuleType("app.utils.finance_utils")
finance_utils_stub.normalize_account_balance = lambda acct: acct
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_utils_stub

# Dispatcher logger for CLI sync test (if needed by your app)
dispatcher_stub = types.ModuleType("app.helpers.account_refresh_dispatcher")
dispatcher_stub.refresh_all_accounts = lambda: []
dispatcher_stub.logger = SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
sys.modules["app.helpers.account_refresh_dispatcher"] = dispatcher_stub

# -------------------------
# Load Blueprint (after all stubs)
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
