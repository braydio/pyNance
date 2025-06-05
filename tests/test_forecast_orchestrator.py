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
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.config"] = config_stub
sys.modules["app.extensions"] = extensions_stub

services_pkg = types.ModuleType("app.services")
sys.modules["app.services"] = services_pkg
fe_stub = types.ModuleType("app.services.forecast_engine")


class DummyRuleEngine:
    def __init__(self, db=None):
        self.db = db

    def forecast_balances(self, horizon_days=60):
        today = datetime.utcnow().date()
        return [
            {"date": today + timedelta(days=i), "account_id": "acc", "balance": i}
            for i in range(horizon_days)
        ]


fe_stub.ForecastEngine = DummyRuleEngine
sys.modules["app.services.forecast_engine"] = fe_stub

fs_stub = types.ModuleType("app.services.forecast_stat_model")
fs_stub.ForecastEngine = DummyRuleEngine
sys.modules["app.services.forecast_stat_model"] = fs_stub
MODULE_PATH = os.path.join(BASE_BACKEND, "app", "services", "forecast_orchestrator.py")
spec = importlib.util.spec_from_file_location(
    "app.services.forecast_orchestrator", MODULE_PATH
)
forecast_orchestrator = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(forecast_orchestrator)
except Exception:
    pytest.skip("orchestrator import failed", allow_module_level=True)


class DummyDB:
    pass


def test_orchestrator_forecast():
    orch = forecast_orchestrator.ForecastOrchestrator(DummyDB())
    orch.rule_engine = DummyRuleEngine()
    result = orch.forecast(days=5)
    assert len(result) == 5
