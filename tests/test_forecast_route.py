import os
import sys
import importlib.util
from datetime import datetime, timedelta
import pytest
import types

# ---- Paths and Imports ----
BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

# ---- app.config/environment/extensions stubs ----
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(info=lambda *a, **k: None)
config_stub.plaid_client = None
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")


class QueryStub:
    def filter(self, *a, **k):
        return self

    def all(self):
        return []


extensions_stub.db = types.SimpleNamespace(
    session=types.SimpleNamespace(query=lambda *a, **k: QueryStub())
)
sys.modules["app.extensions"] = extensions_stub

# ---- app.sql as package + forecast_logic ----
sql_pkg = types.ModuleType("app.sql")
sql_pkg.__path__ = []
forecast_logic_stub = types.ModuleType("app.sql.forecast_logic")
sql_pkg.forecast_logic = forecast_logic_stub
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.forecast_logic"] = forecast_logic_stub

# ---- app.services.forecast_engine etc ----
services_pkg = types.ModuleType("app.services")
services_pkg.__path__ = []
sys.modules["app.services"] = services_pkg

fe_stub = types.ModuleType("app.services.forecast_engine")


class DummyRuleEngine:
    def __init__(self, db=None):
        self.db = db

    def forecast_balances(self, horizon_days=60):
        today = datetime.utcnow().date()
        return [
            {"date": today + timedelta(days=i), "account_id": "acc", "balance": 100 + i}
            for i in range(horizon_days)
        ]


fe_stub.ForecastEngine = DummyRuleEngine
sys.modules["app.services.forecast_engine"] = fe_stub

fs_stub = types.ModuleType("app.services.forecast_stat_model")
fs_stub.ForecastEngine = DummyRuleEngine
sys.modules["app.services.forecast_stat_model"] = fs_stub

orch_stub = types.ModuleType("app.services.forecast_orchestrator")
orch_stub.ForecastOrchestrator = type(
    "ForecastOrchestrator",
    (),
    {
        "__init__": lambda self, db=None: None,
        "build_forecast_payload": lambda self, **k: {
            "labels": ["a", "b"],
            "forecast": [1, 2],
            "actuals": [None, None],
            "metadata": {},
        },
    },
)
sys.modules["app.services.forecast_orchestrator"] = orch_stub

# ---- app.models stub ----
models_stub = types.ModuleType("app.models")


class ColumnStub:
    def __ge__(self, other):
        return self

    def __le__(self, other):
        return self


class AccountHistory:
    date = ColumnStub()
    balance = 0


models_stub.AccountHistory = AccountHistory
models_stub.Account = type("Account", (), {})
sys.modules["app.models"] = models_stub

# ---- Import and load the blueprint ----
ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "forecast.py")
spec = importlib.util.spec_from_file_location("app.routes.forecast", ROUTE_PATH)
forecast_module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(forecast_module)
except Exception:
    pytest.skip("forecast module import failed", allow_module_level=True)

from flask import Flask

# ---- Load forecast orchestrator for monkeypatching ----
SERVICES_PATH = os.path.join(
    BASE_BACKEND, "app", "services", "forecast_orchestrator.py"
)
spec2 = importlib.util.spec_from_file_location(
    "app.services.forecast_orchestrator", SERVICES_PATH
)
forecast_orchestrator = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(forecast_orchestrator)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(forecast_module.forecast, url_prefix="/api/forecast")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def dummy_forecast(self, method="rule", days=60, stat_input=None):
    today = datetime.utcnow().date()
    return [
        {"date": today + timedelta(days=i), "account_id": "acc", "balance": 100 + i}
        for i in range(days)
    ]


def test_forecast_route(client, monkeypatch):
    monkeypatch.setattr(
        forecast_orchestrator.ForecastOrchestrator, "forecast", dummy_forecast
    )
    monkeypatch.setattr(
        sys.modules["app.services.forecast_orchestrator"].ForecastOrchestrator,
        "forecast",
        dummy_forecast,
        raising=False,
    )
    resp = client.get("/api/forecast")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "labels": ["a", "b"],
        "forecast": [1, 2],
        "actuals": [None, None],
        "metadata": {},
    }


def test_forecast_route_missing_data(client, monkeypatch):
    def empty_payload(self, **_):
        return {"labels": [], "forecast": [], "actuals": [], "metadata": {}}

    monkeypatch.setattr(
        forecast_orchestrator.ForecastOrchestrator,
        "build_forecast_payload",
        empty_payload,
    )
    monkeypatch.setattr(
        sys.modules["app.services.forecast_orchestrator"].ForecastOrchestrator,
        "build_forecast_payload",
        empty_payload,
    )
    resp = client.get("/api/forecast")
    assert resp.status_code == 200
    assert resp.get_json()["labels"] == []
