"""Tests for arbitrage API routes."""

import importlib.util
import json
import os
import sys
import types

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(info=lambda *a, **k: None)
sys.modules["app.config"] = config_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

constants_path = os.path.join(BASE_BACKEND, "app", "config", "constants.py")
constants_spec = importlib.util.spec_from_file_location(
    "app.config.constants", constants_path
)
constants_module = importlib.util.module_from_spec(constants_spec)
constants_spec.loader.exec_module(constants_module)  # type: ignore
sys.modules["app.config.constants"] = constants_module

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "arbitrage.py")
spec = importlib.util.spec_from_file_location("app.routes.arbitrage", ROUTE_PATH)
arbitrage_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbitrage_module)  # type: ignore


@pytest.fixture
def client(tmp_path):
    test_file = tmp_path / "arbitrage.json"
    constants_module.ARBITRAGE_FILE = str(test_file)
    test_file.write_text(json.dumps({"value": 5}))
    app = Flask(__name__)
    app.register_blueprint(arbitrage_module.arbitrage, url_prefix="/api/arbitrage")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_current_arbitrage(client):
    resp = client.get("/api/arbitrage/current")
    assert resp.status_code == 200
    assert resp.get_json()["value"] == 5
