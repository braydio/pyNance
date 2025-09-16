import hashlib
import hmac
import importlib.util
import json
import os
import sys
import types

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)

# Ensure a clean slate for stubbed modules
sys.modules.pop("app", None)
sys.modules.pop("app.config", None)
sys.modules.pop("app.extensions", None)
sys.modules.pop("app.helpers", None)
sys.modules.pop("app.helpers.plaid_helpers", None)
sys.modules.pop("app.models", None)
sys.modules.pop("app.services", None)
sys.modules.pop("app.services.plaid_sync", None)
sys.modules.pop("app.sql", None)
sys.modules.pop("app.sql.investments_logic", None)

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
    debug=lambda *a, **k: None,
)
config_stub.PLAID_WEBHOOK_SECRET = "unit_secret"
sys.modules["app.config"] = config_stub

class SessionRecorder:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.rollbacks = 0

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _make_query_result(items):
    return types.SimpleNamespace(all=lambda: list(items))


def _default_query():
    return _make_query_result([])


extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(session=SessionRecorder())
sys.modules["app.extensions"] = extensions_stub

helpers_pkg = types.ModuleType("app.helpers")
helpers_stub = types.ModuleType("app.helpers.plaid_helpers")
helpers_stub.get_investment_transactions = lambda *a, **k: []
helpers_pkg.plaid_helpers = helpers_stub
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.plaid_helpers"] = helpers_stub

class DummyPlaidAccount:
    query = types.SimpleNamespace(filter_by=lambda **kwargs: _default_query())

    def __init__(self, account_id, item_id, product="transactions", account=None):
        self.account_id = account_id
        self.item_id = item_id
        self.product = product
        self.access_token = f"tok-{account_id}"
        self.account = account


class DummyPlaidWebhookLog:
    def __init__(self, **kwargs):
        self.data = kwargs


models_stub = types.ModuleType("app.models")
models_stub.PlaidAccount = DummyPlaidAccount
models_stub.PlaidWebhookLog = DummyPlaidWebhookLog
sys.modules["app.models"] = models_stub

services_pkg = types.ModuleType("app.services")
services_stub = types.ModuleType("app.services.plaid_sync")
services_stub.sync_account_transactions = lambda account_id: {
    "account_id": account_id
}
services_pkg.plaid_sync = services_stub
sys.modules["app.services"] = services_pkg
sys.modules["app.services.plaid_sync"] = services_stub

investments_logic_stub = types.ModuleType("app.sql.investments_logic")
investments_logic_stub.upsert_investment_transactions = lambda txs: len(txs)
investments_logic_stub.upsert_investments_from_plaid = (
    lambda user_id, token: {"holdings": 0}
)
sql_pkg = types.ModuleType("app.sql")
sql_pkg.investments_logic = investments_logic_stub
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.investments_logic"] = investments_logic_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "plaid_webhook.py")
spec = importlib.util.spec_from_file_location(
    "app.routes.plaid_webhook", ROUTE_PATH
)
plaid_webhook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plaid_webhook)


@pytest.fixture
def client(monkeypatch):
    session = SessionRecorder()
    monkeypatch.setattr(plaid_webhook.db, "session", session, raising=False)
    monkeypatch.setattr(
        plaid_webhook.PlaidAccount,
        "query",
        types.SimpleNamespace(filter_by=lambda **kwargs: _default_query()),
        raising=False,
    )
    monkeypatch.setattr(plaid_webhook, "PLAID_WEBHOOK_SECRET", "unit_secret")

    app = Flask(__name__)
    app.register_blueprint(plaid_webhook.plaid_webhooks, url_prefix="/api/webhooks")
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client, session


def _signed_headers(secret: str, body: str, timestamp: str = "1234567890"):
    digest = hmac.new(
        secret.encode("utf-8"),
        msg=f"{timestamp}.{body}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return {"Plaid-Signature": f"t={timestamp},v1={digest}"}


def test_missing_secret_returns_500(client, monkeypatch):
    test_client, session = client
    monkeypatch.setattr(plaid_webhook, "PLAID_WEBHOOK_SECRET", "")
    body = json.dumps({"webhook_type": "TRANSACTIONS"})

    response = test_client.post(
        "/api/webhooks/plaid", data=body, content_type="application/json"
    )

    assert response.status_code == 500
    payload = response.get_json()
    assert payload["status"] == "error"
    assert session.commits == 0
    assert session.added == []


def test_missing_signature_returns_400(client):
    test_client, session = client
    body = json.dumps({"webhook_type": "TRANSACTIONS"})

    response = test_client.post(
        "/api/webhooks/plaid", data=body, content_type="application/json"
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid_signature"
    assert session.commits == 0
    assert session.added == []


def test_invalid_signature_returns_400(client):
    test_client, session = client
    body = json.dumps({"webhook_type": "TRANSACTIONS"})

    response = test_client.post(
        "/api/webhooks/plaid",
        data=body,
        content_type="application/json",
        headers={"Plaid-Signature": "t=1,v1=invalid"},
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid_signature"
    assert session.commits == 0
    assert session.added == []


def test_valid_signature_allows_processing(client, monkeypatch):
    test_client, session = client
    payload = {
        "webhook_type": "TRANSACTIONS",
        "webhook_code": "DEFAULT_UPDATE",
        "item_id": "item-42",
    }
    body = json.dumps(payload, separators=(",", ":"))
    headers = _signed_headers("unit_secret", body)

    monkeypatch.setattr(
        plaid_webhook.PlaidAccount,
        "query",
        types.SimpleNamespace(
            filter_by=lambda **kwargs: _make_query_result([])
        ),
        raising=False,
    )

    response = test_client.post(
        "/api/webhooks/plaid",
        data=body,
        content_type="application/json",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert session.commits == 1
    assert len(session.added) == 1
    assert isinstance(session.added[0], DummyPlaidWebhookLog)
    assert session.rollbacks == 0
