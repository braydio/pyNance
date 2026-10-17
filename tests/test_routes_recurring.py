import importlib.util
import os
import sys
import types
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from flask import Flask

# Patch 'app' into sys.modules so Flask can load Blueprints
pkg = types.ModuleType("app")
pkg.__path__ = [os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "backend", "app")]
sys.modules["app"] = pkg

_orig_extensions = sys.modules.get("app.extensions")
# ------------------------------
# Environment Setup
# ------------------------------

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub
finance_stub = types.ModuleType("app.utils.finance_utils")
finance_stub.display_transaction_amount = lambda tx: getattr(tx, "amount", 0)
sys.modules["app.utils.finance_utils"] = finance_stub


@pytest.fixture(autouse=True)
def restore_modules():
    yield
    if _orig_extensions is not None:
        sys.modules["app.extensions"] = _orig_extensions
    else:
        sys.modules.pop("app.extensions", None)


models_stub = types.ModuleType("app.models")


class DummyTransaction:
    def __init__(self):
        self.amount = 1.0
        self.description = "d"
        self.merchant_name = ""
        self.date = datetime.now(timezone.utc)
        self.account_id = "acc1"


class DummyRecurring:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


models_stub.Transaction = DummyTransaction
models_stub.RecurringTransaction = DummyRecurring
sys.modules["app.models"] = models_stub

services_stub = types.ModuleType("app.services")
sys.modules["app.services"] = services_stub

bridge_stub = types.ModuleType("app.services.recurring_bridge")


class DummyBridge:
    def __init__(self, txs):
        self.txs = txs

    @staticmethod
    def sync_to_db():
        return [{"mock": "action"}]


bridge_stub.RecurringBridge = DummyBridge
sys.modules["app.services.recurring_bridge"] = bridge_stub

# ------------------------------
# Load Route Module
# ------------------------------

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


# ------------------------------
# Test: POST /scan/<account_id>
# ------------------------------


def test_scan_route_returns_list(client, monkeypatch):
    # Mock Transaction.query behavior
    mock_query = MagicMock()
    mock_tx = MagicMock(
        amount=1.0,
        description="d",
        merchant_name="",
        date=datetime.now(timezone.utc),
        account_id="acc1",  # ✅ Required field
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
        recurring_module,
        "get_structured_recurring",
        lambda account_id: {"status": "success", "reminders": []},
    )

    resp = client.post("/api/recurring/scan/acc1")
    assert resp.status_code == 200
    assert isinstance(resp.get_json()["reminders"], list)


def test_get_structured_recurring_includes_confidence_metadata(client, monkeypatch):
    today = recurring_module.date.today()
    latest_date = today - recurring_module.timedelta(days=3)
    auto_row = types.SimpleNamespace(
        description="Rent",
        amount=-1200.0,
        occurrences=4,
        latest_date=latest_date,
    )

    mock_auto_query = MagicMock()
    mock_auto_query.filter.return_value = mock_auto_query
    mock_auto_query.group_by.return_value = mock_auto_query
    mock_auto_query.having.return_value = mock_auto_query
    mock_auto_query.all.return_value = [auto_row]

    mock_db = types.SimpleNamespace(session=types.SimpleNamespace(query=MagicMock(return_value=mock_auto_query)))
    monkeypatch.setattr(recurring_module, "db", mock_db)

    mock_transaction_model = MagicMock()
    mock_transaction_model.account_id = "account_id"
    mock_transaction_model.date = "date"
    mock_transaction_model.id = "id"
    mock_transaction_model.description = "description"
    mock_transaction_model.amount = "amount"
    monkeypatch.setattr(recurring_module, "Transaction", mock_transaction_model)

    mock_recurring_query = MagicMock()
    mock_recurring_query.filter_by.return_value = mock_recurring_query
    mock_recurring_query.all.return_value = []
    mock_recurring_model = MagicMock()
    mock_recurring_model.query = mock_recurring_query
    monkeypatch.setattr(recurring_module, "RecurringTransaction", mock_recurring_model)

    response = client.get("/api/recurring/acc1/recurring")
    assert response.status_code == 200
    payload = response.get_json()
    reminder = payload["reminders"][0]
    assert reminder["source"] == "auto"
    assert reminder["auto_detection"]["occurrences"] == 4
    assert 0 <= reminder["auto_detection"]["confidence_score"] <= 100
    assert reminder["account_id"] == "acc1"
