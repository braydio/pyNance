"""Tests for Teller link-token and accounts endpoints."""

import importlib.util
import os
import sys
import types

import pytest
from flask import Flask

# -------------------- PATH & MODULE STUBS --------------------
BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# --- Config stub ---
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FILES = {
    "TELLER_DOT_KEY": "dummy",
    "TELLER_DOT_CERT": "",
    "TELLER_ACCOUNTS": "",
}
config_stub.TELLER_APP_ID = "app123"
config_stub.TELLER_API_BASE_URL = "https://example.com"
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

# --- Helper stub ---
helpers_pkg = types.ModuleType("app.helpers")
helpers_pkg.teller_helpers = types.ModuleType("app.helpers.teller_helpers")
helpers_pkg.teller_helpers.load_tokens = lambda: []
helpers_pkg.teller_helpers.save_tokens = lambda tokens: None
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.teller_helpers"] = helpers_pkg.teller_helpers

# --- Extensions stub ---
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

# --- Models stub ---
models_stub = types.ModuleType("app.models")
models_stub.TellerAccount = type("TellerAccount", (), {})
sys.modules["app.models"] = models_stub

# --- Account Logic stub ---
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.get_accounts_from_db = lambda: [{"account_id": "a1"}]
sql_pkg = types.ModuleType("app.sql")
sql_pkg.__path__ = []
sql_pkg.account_logic = account_logic_stub
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub

# -------------------- LOAD ROUTE UNDER TEST --------------------
ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "teller.py")
spec = importlib.util.spec_from_file_location("app.routes.teller", ROUTE_PATH)
teller_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(teller_module)  # type: ignore[union-attr]


# -------------------- TESTS --------------------
@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(teller_module.link_teller, url_prefix="/api/teller")
    app.config["TESTING"] = True
    app.secret_key = "test"
    with app.test_client() as c:
        yield c


def test_generate_link_token_sends_user_id(client, monkeypatch):
    captured = {}

    class DummyResp:
        status_code = 200

        @staticmethod
        def json():
            return {"link_token": "abc"}

        text = "{}"

    def fake_post(url, headers=None, json=None):
        captured["payload"] = json
        return DummyResp()

    monkeypatch.setattr(teller_module.requests, "post", fake_post)

    resp = client.post("/api/teller/link-token", json={"user_id": "u1"})
    assert resp.status_code == 200
    assert captured["payload"]["user_id"] == "u1"
    data = resp.get_json()
    assert data["link_token"] == "abc"


def test_generate_link_token_uses_session(client, monkeypatch):
    captured = {}

    class DummyResp:
        status_code = 200

        @staticmethod
        def json():
            return {"link_token": "xyz"}

        text = "{}"

    def fake_post(url, headers=None, json=None):
        captured["payload"] = json
        return DummyResp()

    monkeypatch.setattr(teller_module.requests, "post", fake_post)

    with client.session_transaction() as sess:
        sess["user_id"] = "sess1"

    resp = client.post("/api/teller/link-token")
    assert resp.status_code == 200
    assert captured["payload"]["user_id"] == "sess1"


def test_get_accounts_returns_db_values(client, monkeypatch):
    # Patch the account logic stub method (should already exist from sys.modules)
    monkeypatch.setitem(
        teller_module.__dict__,
        "get_accounts_from_db",
        lambda: [{"account_id": "a1"}],
    )
    monkeypatch.setattr(
        teller_module.account_logic,
        "get_accounts_from_db",
        lambda: [{"account_id": "a1"}],
    )
    resp = client.get("/api/teller/accounts")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["data"]["accounts"][0]["account_id"] == "a1"
