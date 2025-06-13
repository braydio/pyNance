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
    info=lambda *args, **kwargs: None,
    debug=lambda *args, **kwargs: None,
    warning=lambda *args, **kwargs: None,
    error=lambda *args, **kwargs: None,
)

sys.modules["app.config"] = config_pkg


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
    assert resp.status_code in {200, 400}
