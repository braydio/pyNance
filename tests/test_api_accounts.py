import os
import sys
import types
import importlib.util
from flask import Flask
import pytest

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# Stub config
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.plaid_client = None
config_stub.TELLER_API_BASE_URL = "https://example.com"
config_stub.FILES = {}
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

# Helpers stub
helpers_pkg = types.ModuleType("app.helpers")
teller_helpers_stub = types.ModuleType("app.helpers.teller_helpers")
teller_helpers_stub.load_tokens = lambda: []
helpers_pkg.teller_helpers = teller_helpers_stub
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.teller_helpers"] = teller_helpers_stub

# SQL stub
sql_pkg = types.ModuleType("app.sql")
forecast_logic_stub = types.ModuleType("app.sql.forecast_logic")
forecast_logic_stub.update_account_history = lambda *a, **k: None
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.refresh_data_for_plaid_account = lambda *a, **k: True
account_logic_stub.refresh_data_for_teller_account = lambda *a, **k: True
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.forecast_logic"] = forecast_logic_stub
sys.modules["app.sql.account_logic"] = account_logic_stub
sql_pkg.account_logic = account_logic_stub

# Utils stub
utils_pkg = types.ModuleType("app.utils")
finance_stub = types.ModuleType("app.utils.finance_utils")
finance_stub.normalize_account_balance = lambda bal, typ: bal
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_stub

# Models stub
models_stub = types.ModuleType("app.models")


class DummyAccount:
    class Column:
        def is_(self, _):
            return self

    is_hidden = Column()


models_stub.Account = DummyAccount
models_stub.AccountHistory = type("AccountHistory", (), {})
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "accounts.py")
spec = importlib.util.spec_from_file_location("app.routes.accounts", ROUTE_PATH)
accounts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts_module)


class QueryStub:
    def __init__(self, accounts):
        self._accounts = list(accounts)

    def filter(self, *a, **k):
        self._accounts = [
            acc for acc in self._accounts if not getattr(acc, "is_hidden", False)
        ]
        return self

    def all(self):
        return self._accounts


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(accounts_module.accounts, url_prefix="/api/accounts")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_accounts_default_filters_hidden(client, monkeypatch):
    sample_accounts = [
        DummyAccount(),
        DummyAccount(),
    ]
    sample_accounts[0].id = 1
    sample_accounts[0].account_id = "a1"
    sample_accounts[0].name = "Acc1"
    sample_accounts[0].institution_name = "Bank"
    sample_accounts[0].type = "checking"
    sample_accounts[0].balance = 100
    sample_accounts[0].subtype = "checking"
    sample_accounts[0].link_type = "manual"
    sample_accounts[0].is_hidden = False
    sample_accounts[0].plaid_account = None
    sample_accounts[0].teller_account = None

    sample_accounts[1].id = 2
    sample_accounts[1].account_id = "a2"
    sample_accounts[1].name = "Acc2"
    sample_accounts[1].institution_name = "Bank"
    sample_accounts[1].type = "checking"
    sample_accounts[1].balance = 200
    sample_accounts[1].subtype = "checking"
    sample_accounts[1].link_type = "manual"
    sample_accounts[1].is_hidden = True
    sample_accounts[1].plaid_account = None
    sample_accounts[1].teller_account = None

    accounts_module.Account.query = QueryStub(sample_accounts)
    resp = client.get("/api/accounts/get_accounts")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "accounts" in data
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["account_id"] == "a1"


def test_get_accounts_include_hidden(client, monkeypatch):
    sample_accounts = [
        DummyAccount(),
        DummyAccount(),
    ]
    for idx, acc in enumerate(sample_accounts, start=1):
        acc.id = idx
        acc.account_id = f"a{idx}"
        acc.name = f"Acc{idx}"
        acc.institution_name = "Bank"
        acc.type = "checking"
        acc.balance = idx * 100
        acc.subtype = "checking"
        acc.link_type = "manual"
        acc.is_hidden = False
        acc.plaid_account = None
        acc.teller_account = None

    accounts_module.Account.query = QueryStub(sample_accounts)
    resp = client.get("/api/accounts/get_accounts?include_hidden=true")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["accounts"]) == 2
