import os
import sys
import importlib.util
import types

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)
app_pkg = types.ModuleType("app")
sys.modules["app"] = app_pkg

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
session_ns = types.SimpleNamespace(commit=lambda: None, rollback=lambda: None)
extensions_stub.db = types.SimpleNamespace(session=session_ns, commit=lambda: None, rollback=lambda: None)
sys.modules["app.extensions"] = extensions_stub

# Helpers stub
helpers_pkg = types.ModuleType("app.helpers")
teller_helpers_stub = types.ModuleType("app.helpers.teller_helpers")
teller_helpers_stub.load_tokens = lambda: [{"user_id": "u1", "access_token": "tok"}]
helpers_pkg.teller_helpers = teller_helpers_stub
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.teller_helpers"] = teller_helpers_stub

# Utils stub
utils_pkg = types.ModuleType("app.utils")
finance_utils_stub = types.ModuleType("app.utils.finance_utils")
finance_utils_stub.normalize_account_balance = lambda bal, t: bal
utils_pkg.finance_utils = finance_utils_stub
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_utils_stub

# SQL stub
sql_pkg = types.ModuleType("app.sql")
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.refresh_data_for_plaid_account = lambda *a, **k: True
account_logic_stub.refresh_data_for_teller_account = lambda *a, **k: True
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sql_pkg.account_logic = account_logic_stub

# Models stub
models_stub = types.ModuleType("app.models")


class DummyAccount:
    def __init__(self, aid, link_type="Plaid"):
        self.account_id = aid
        self.name = aid
        self.type = "checking"
        self.subtype = "checking"
        self.balance = 0
        self.link_type = link_type
        self.user_id = "u1"
        self.plaid_account = types.SimpleNamespace(access_token="tok", last_refreshed=None) if link_type == "Plaid" else None
        self.teller_account = types.SimpleNamespace(access_token="tok", last_refreshed=None) if link_type == "Teller" else None


class DummyInstitution:
    def __init__(self, iid, accounts):
        self.id = iid
        self.name = f"Inst {iid}"
        self.provider = "manual"
        self.accounts = accounts
        self.last_refreshed = None


class InstQuery:
    def __init__(self, insts):
        self.insts = {i.id: i for i in insts}

    def all(self):
        return list(self.insts.values())

    def get_or_404(self, iid):
        return self.insts[iid]


models_stub.Institution = DummyInstitution
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "institutions.py")
spec = importlib.util.spec_from_file_location("app.routes.institutions", ROUTE_PATH)
inst_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inst_module)


@pytest.fixture
def client():
    inst1 = DummyInstitution(1, [DummyAccount("a1"), DummyAccount("a2", "Teller")])
    inst2 = DummyInstitution(2, [DummyAccount("a3")])
    inst_module.Institution.query = InstQuery([inst1, inst2])

    app = Flask(__name__)
    app.register_blueprint(inst_module.institutions, url_prefix="/api/institutions")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_institutions(client):
    resp = client.get("/api/institutions/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert len(data["institutions"]) == 2


def test_refresh_institution(client):
    resp = client.post("/api/institutions/1/refresh", json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["updated_accounts"] == ["a1", "a2"]
