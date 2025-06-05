import os
import sys
import importlib.util
from datetime import datetime, timedelta

import pytest

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)
import types
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(info=lambda *a, **k: None)
config_stub.plaid_client = None
config_stub.FLASK_ENV = "test"
env_stub = types.ModuleType("app.config.environment")
sys.modules["app.config.environment"] = env_stub
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.config"] = config_stub
sys.modules["app.extensions"] = extensions_stub
ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "forecast.py")
spec = importlib.util.spec_from_file_location("forecast_module", ROUTE_PATH)
forecast_module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(forecast_module)
except Exception:  # pragma: no cover - skip if deps missing
    pytest.skip("forecast module import failed", allow_module_level=True)
from flask import Flask
SERVICES_PATH = os.path.join(BASE_BACKEND, "app", "services", "forecast_orchestrator.py")
spec2 = importlib.util.spec_from_file_location("forecast_orchestrator", SERVICES_PATH)
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
    resp = client.get("/api/forecast")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "labels" in data
    assert "forecast" in data
    assert len(data["labels"]) == len(data["forecast"])
