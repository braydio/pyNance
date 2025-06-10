import os
import sys
import types
import importlib.util
from datetime import datetime, UTC
from flask import Flask, jsonify
from unittest.mock import MagicMock
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
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
sys.modules["app.models"] = models_stub

# ------------------------------
# Mock: app.services.recurring_bridge
# ------------------------------

services_pkg = types.ModuleType("app.services")
sys.modules["app.services"] = services_pkg

bridge_stub = types.ModuleType("app.services.recurring_bridge")
sys.modules["app.services.recurring_bridge"] = bridge_stub

# ------------------------------
# Load Target Route Module
# ------------------------------

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "recurring.py")
spec = importlib.util.spec_from_file_location("app.routes.recurring", ROUTE_PATH)
recurring_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recurring_module)

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
    # Patch Transaction model and query
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
    # Patch class-level .date to support `.filter(Transaction.date >= cutoff)`
    mock_transaction_model.date = MagicMock()
    mock_transaction_model.date.__ge__.return_value = True
    monkeypatch.setattr(recurring_module, "Transaction", mock_transaction_model)

    # Patch RecurringBridge
    mock_bridge_class = MagicMock()
    mock_bridge_instance = MagicMock()
    mock_bridge_instance.sync_to_db.return_value = [{"mock": "action"}]
    mock_bridge_class.return_value = mock_bridge_instance
    monkeypatch.setattr(recurring_module, "RecurringBridge", mock_bridge_class)

    # Patch reminder response
    monkeypatch.setattr(
        recurring_module,
        "get_structured_recurring",
        lambda account_id: jsonify({"status": "success", "reminders": []}),
    )

    resp = client.post("/api/recurring/scan/acc1")
    assert resp.status_code == 200
    assert isinstance(resp.get_json()["reminders"], list)
