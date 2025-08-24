import importlib.util
import os
import sys
import types
from datetime import date

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


class _DummyField:
    def __ge__(self, other):
        return self

    def __le__(self, other):
        return self

    def is_(self, other):
        return self

    def __or__(self, other):
        return self


dummy_field = _DummyField()
models_stub.Transaction = type(
    "Transaction", (), {"date": dummy_field, "is_internal": dummy_field}
)
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "summary.py")
spec = importlib.util.spec_from_file_location("app.routes.summary", ROUTE_PATH)
summary_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary_module)


@pytest.fixture
def client(monkeypatch):
    mock_transactions = [
        types.SimpleNamespace(date=date(2024, 1, 1), amount=100, is_internal=False),
        types.SimpleNamespace(date=date(2024, 1, 2), amount=-200, is_internal=False),
        types.SimpleNamespace(date=date(2024, 1, 3), amount=300, is_internal=False),
    ]

    query = types.SimpleNamespace(
        filter=lambda *a, **k: query,
        filter_by=lambda **k: query,
        all=lambda: mock_transactions,
    )
    monkeypatch.setattr(
        summary_module.db,
        "session",
        types.SimpleNamespace(query=lambda model: query),
        raising=False,
    )
    monkeypatch.setattr(
        summary_module,
        "display_transaction_amount",
        lambda tx: tx.amount,
        raising=False,
    )

    app = Flask(__name__)
    app.register_blueprint(summary_module.summary, url_prefix="/api/summary")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_financial_summary_metrics(client):
    resp = client.get(
        "/api/summary/financial?start_date=2024-01-01&end_date=2024-01-03"
    )
    assert resp.status_code == 200
    payload = resp.get_json()["data"]
    assert payload["highestIncomeDay"]["date"] == "2024-01-03"
    assert payload["highestExpenseDay"]["date"] == "2024-01-02"
    assert "trend" in payload
    assert "volatility" in payload
    assert isinstance(payload["outliers"], list)
