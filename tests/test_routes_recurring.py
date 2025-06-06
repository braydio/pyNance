import os
import sys
import types
import importlib.util
from datetime import datetime
from flask import Flask
import pytest

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# minimal stubs
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


models_stub.Transaction = DummyTx
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
sys.modules["app.models"] = models_stub

services_pkg = types.ModuleType("app.services")
sys.modules["app.services"] = services_pkg

bridge_stub = types.ModuleType("app.services.recurring_bridge")


class DummyBridge:
    def __init__(self, txs):
        self.txs = txs

    def sync_to_db(self):
        return []


bridge_stub.RecurringBridge = DummyBridge
sys.modules["app.services.recurring_bridge"] = bridge_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "recurring.py")
spec = importlib.util.spec_from_file_location("app.routes.recurring", ROUTE_PATH)
recurring_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recurring_module)


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


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(recurring_module.recurring, url_prefix="/api/recurring")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_scan_route_returns_list(client, monkeypatch):
    dummy_tx = models_stub.Transaction()
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
