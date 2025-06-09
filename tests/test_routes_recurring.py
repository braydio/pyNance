import os
import sys
import types
import importlib.util
from datetime import datetime
from flask import Flask
import pytest

# ------------------------------
# Environment Setup
# ------------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Ensure clean re-import of app module
sys.modules.pop("app", None)

# ------------------------------
# Mock: app.config and environment
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

env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

models_stub = types.ModuleType("app.models")


class DummyTx:
    class DateAttr:
        def __ge__(self, other):
            return True

        def desc(self):
            return self

    date = DateAttr()

    def __init__(self):
        self.amount = 1.0
        self.description = "d"
        self.merchant_name = ""
        self.date = datetime.utcnow()


class DummyRecurring:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


models_stub.Transaction = DummyTransaction
models_stub.RecurringTransaction = DummyRecurring
sys.modules["app.models"] = models_stub

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

ROUTE_PATH = os.path.join(BASE_DIR, "app", "routes", "recurring.py")
spec = importlib.util.spec_from_file_location("app.routes.recurring", ROUTE_PATH)
recurring_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recurring_module)

# ------------------------------
# Flask Test Client Fixture
# ------------------------------


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(recurring_module.recurring, url_prefix="/api/recurring")
    with app.test_client() as client:
        yield client


def test_scan_route_returns_list(client, monkeypatch):
    # Mock Transaction.query behavior
    mock_query = MagicMock()
    mock_tx = MagicMock(
        amount=1.0, description="d", merchant_name="", date=datetime.now(UTC)
    )
    mock_query.filter_by.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [mock_tx]

    mock_transaction_model = MagicMock()
    mock_transaction_model.query = mock_query
    mock_transaction_model.date = MagicMock()
    mock_transaction_model.date.__ge__.return_value = True
    monkeypatch.setattr(recurring_module, "Transaction", mock_transaction_model)

    # Mock RecurringBridge
    mock_bridge_class = MagicMock()
    mock_bridge_instance = MagicMock()
    mock_bridge_instance.sync_to_db.return_value = [{"mock": "action"}]
    mock_bridge_class.return_value = mock_bridge_instance
    monkeypatch.setattr(recurring_module, "RecurringBridge", mock_bridge_class)

    # Mock get_structured_recurring
    monkeypatch.setattr(
        recurring_module.Transaction,
        "query",
        QueryStub([dummy_tx]),
        raising=False,
    )
    monkeypatch.setattr(recurring_module, "RecurringBridge", DummyBridge)
    resp = client.post("/api/recurring/scan/acc1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data.get("actions"), list)
