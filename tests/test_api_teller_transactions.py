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

# Config stub
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FILES = {}
config_stub.TELLER_API_BASE_URL = "https://example.com"
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

# Helpers stub
helpers_pkg = types.ModuleType("app.helpers")
teller_helpers_stub = types.ModuleType("app.helpers.teller_helpers")
teller_helpers_stub.load_tokens = lambda: []
helpers_pkg.teller_helpers = teller_helpers_stub
sys.modules["app.helpers"] = helpers_pkg
sys.modules["app.helpers.teller_helpers"] = teller_helpers_stub

# SQL package and logic
sql_pkg = types.ModuleType("app.sql")
account_logic_stub = types.ModuleType("app.sql.account_logic")


def fake_get_paginated(page, page_size, start_date=None, end_date=None, category=None):
    return [{"id": "t1"}], 1


account_logic_stub.get_paginated_transactions = fake_get_paginated
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sql_pkg.account_logic = account_logic_stub

models_stub = types.ModuleType("app.models")
models_stub.Account = type("Account", (), {})
models_stub.Transaction = type("Transaction", (), {})
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "teller_transactions.py")
spec = importlib.util.spec_from_file_location(
    "app.routes.teller_transactions", ROUTE_PATH
)
teller_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(teller_module)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(teller_module.teller_transactions, url_prefix="/api/teller")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_transactions_filters_passed(client, monkeypatch):
    captured = {}

    def capture_args(page, page_size, start_date=None, end_date=None, category=None):
        captured["start_date"] = start_date
        captured["end_date"] = end_date
        captured["category"] = category
        return [{"id": "tx"}], 1

    monkeypatch.setattr(
        teller_module.account_logic, "get_paginated_transactions", capture_args
    )
    resp = client.get(
        "/api/teller/get_transactions?start_date=2024-01-01&end_date=2024-02-01&category=Food"
    )
    assert resp.status_code == 200
    assert captured["start_date"] == datetime.strptime("2024-01-01", "%Y-%m-%d").date()
    assert captured["end_date"] == datetime.strptime("2024-02-01", "%Y-%m-%d").date()
    assert captured["category"] == "Food"
