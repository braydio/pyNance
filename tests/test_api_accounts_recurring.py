import importlib.util
import os
import sys
import types
from datetime import date, datetime

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)
sys.modules["flask_cors"] = types.SimpleNamespace(CORS=lambda app: app)
sys.modules["flask_migrate"] = types.SimpleNamespace(Migrate=lambda *a, **k: None)

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FLASK_ENV = "test"
config_stub.plaid_client = None
sys.modules["app.config"] = config_stub

env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

models_stub = types.ModuleType("app.models")
models_stub.Account = type("Account", (), {})
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
models_stub.Transaction = type("Transaction", (), {})
models_stub.AccountHistory = type("AccountHistory", (), {})
sys.modules["app.models"] = models_stub

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


def test_get_recurring_uses_display_amount(client, monkeypatch):
    mock_tx = types.SimpleNamespace(
        id=1,
        description="Bill",
        frequency="monthly",
        next_due_date=date(2024, 1, 1),
        notes="",
        updated_at=datetime(2024, 1, 1),
        transaction=types.SimpleNamespace(amount=10.0, transaction_type="expense"),
    )
    query = types.SimpleNamespace(
        filter_by=lambda **kwargs: types.SimpleNamespace(all=lambda: [mock_tx])
    )
    monkeypatch.setattr(
        accounts_module.RecurringTransaction, "query", query, raising=False
    )

    resp = client.get("/api/accounts/acc1/recurring")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["reminders"][0]["amount"] == -10.0
