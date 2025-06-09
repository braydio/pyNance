import os
import sys
import types
import importlib.util
from datetime import datetime, UTC
from flask import Flask, jsonify
import pytest

# ------------------------------
# Setup Paths and Base Stubs
# ------------------------------

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# ------------------------------
# Mock: app.config
# ------------------------------

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

# ------------------------------
# Mock: app.config.environment
# ------------------------------

env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

# ------------------------------
# Mock: app.extensions
# ------------------------------

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

# ------------------------------
# Mock: app.models
# ------------------------------

models_stub = types.ModuleType("app.models")


class DummyTx:
    def __init__(self):
        self.amount = 1.0
        self.description = "d"
        self.merchant_name = ""
        self.date = datetime.now(UTC)


class DummyRecurring:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


models_stub.Transaction = DummyTransaction
models_stub.RecurringTransaction = DummyRecurring
sys.modules["app.models"] = models_stub

# ------------------------------
# Mock: app.services.recurring_bridge
# ------------------------------

services_pkg = types.ModuleType("app.services")
sys.modules["app.services"] = services_pkg

bridge_stub = types.ModuleType("app.services.recurring_bridge")


class DummyBridge:
    def __init__(self, txs):
        self.txs = txs

    def sync_to_db(self):
        return [{"mock": "action"}]


bridge_stub.RecurringBridge = DummyBridge
sys.modules["app.services.recurring_bridge"] = bridge_stub


class DummyBridge:
    def __init__(self, txs):
        self.txs = txs

    def sync_to_db(self):
        return []


bridge_stub.RecurringBridge = DummyBridge
sys.modules["app.services.recurring_bridge"] = bridge_stub

# ------------------------------
# Load Target Route Module
# ------------------------------

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "recurring.py")
spec = importlib.util.spec_from_file_location("app.routes.recurring", ROUTE_PATH)
recurring_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recurring_module)

# ------------------------------
# Query Stub
# ------------------------------


class QueryStub:
    def __init__(self, results):
        self._results = results

    def filter_by(self, *a, **k):
        return self

    def filter(self, *a, **k):
        return self

    def order_by(self, *a, **k):
        return self

    def all(self):
        return self._results


# ------------------------------
# Test Client Fixture
# ------------------------------


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(recurring_module.recurring, url_prefix="/api/recurring")
    with app.test_client() as client:
        yield client


# ------------------------------
# Test: POST /scan/<account_id>
# ------------------------------


def test_scan_route_returns_list(client, monkeypatch):
    dummy_tx = models_stub.Transaction()
    monkeypatch.setattr(
        recurring_module,
        "Transaction",
        type("Transaction", (), {"query": QueryStub([dummy_tx])}),
    )

    monkeypatch.setattr(recurring_module, "RecurringBridge", DummyBridge)

    monkeypatch.setattr(
        recurring_module,
        "get_structured_recurring",
        lambda account_id: jsonify({"status": "success", "reminders": []}),
    )

    resp = client.post("/api/recurring/scan/acc1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data.get("reminders"), list)
