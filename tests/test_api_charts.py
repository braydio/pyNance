"""Tests for charts API endpoints."""

# mypy: ignore-errors

import importlib.util
import os
import sys
import types
from datetime import datetime

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
# Ensure clean import state
sys.modules.pop("app", None)

# Config stub
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

# Environment stub
env_stub = types.ModuleType("app.config.environment")
env_stub.TELLER_WEBHOOK_SECRET = "dummy"
sys.modules["app.config.environment"] = env_stub

# Extensions stub
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

# Services stub
services_pkg = types.ModuleType("app.services")
services_pkg.__path__ = []
sys.modules["app.services"] = services_pkg
fo_stub = types.ModuleType("app.services.forecast_orchestrator")
fo_stub.ForecastOrchestrator = type("ForecastOrchestrator", (), {})
sys.modules["app.services.forecast_orchestrator"] = fo_stub

# Utils stub
utils_pkg = types.ModuleType("app.utils")
finance_stub = types.ModuleType("app.utils.finance_utils")
finance_stub.normalize_account_balance = lambda bal, typ: bal
utils_pkg.finance_utils = finance_stub
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_stub

# Models stub
models_stub = types.ModuleType("app.models")


class DummyAccount:
    account_id = "acc"

    class Column:
        def is_(self, _):
            return self

        def __or__(self, other):
            return self

    is_hidden = Column()

    def __init__(self, balance, typ):
        self.balance = balance
        self.type = typ
        self.created_at = datetime.now()
        self.is_hidden = False


models_stub.Account = DummyAccount
models_stub.Category = type("Category", (), {})


class DummyTransaction:
    id = 1
    account_id = "acc"
    amount = 0.0
    date = datetime.now()


models_stub.Transaction = DummyTransaction
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "charts.py")
spec = importlib.util.spec_from_file_location("app.routes.charts", ROUTE_PATH)
charts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(charts_module)

CATEGORIES_PATH = os.path.join(BASE_BACKEND, "app", "routes", "categories.py")
spec_cats = importlib.util.spec_from_file_location(
    "app.routes.categories", CATEGORIES_PATH
)
categories_module = importlib.util.module_from_spec(spec_cats)
spec_cats.loader.exec_module(categories_module)


class QueryStub:
    def __init__(self, rows):
        self.rows = list(rows)

    def join(self, *a, **k):
        return self

    def filter(self, *a, **k):
        return self

    def with_entities(self, *a, **k):
        return self

    def group_by(self, *a, **k):
        return self

    def order_by(self, *a, **k):
        return self

    def all(self):
        return self.rows


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(charts_module.charts, url_prefix="/api/charts")
    app.register_blueprint(categories_module.categories, url_prefix="/api/categories")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_net_assets_returns_data(client):
    accounts = [DummyAccount(100, "checking"), DummyAccount(-50, "credit")]
    query = QueryStub(accounts)
    extensions_stub.db.session = types.SimpleNamespace(query=lambda *a, **k: query)
    resp = client.get("/api/charts/net_assets")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert len(data["data"]) == 6
    assert any(entry["net_assets"] != 0 for entry in data["data"])


class AggRow:
    def __init__(self, period, income, expenses, txn_count):
        self.period = period
        self.income = income
        self.expenses = expenses
        self.txn_count = txn_count


def test_get_cash_flow_returns_aggregated_rows(client):
    rows = [
        AggRow("01-2024", 100.0, 50.0, 2),
        AggRow("02-2024", 200.0, 80.0, 3),
    ]
    query = QueryStub(rows)
    extensions_stub.db.session = types.SimpleNamespace(query=lambda *a, **k: query)
    resp = client.get("/api/charts/cash_flow")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert len(data["data"]) == 2
    assert data["metadata"]["total_transactions"] == 5


def test_category_breakdown_tree_totals_match(client):
    class DummyCat:
        def __init__(self, id_, parent_id=None, primary=None, detailed=None):
            self.id = id_
            self.parent_id = parent_id
            self.primary_category = primary
            self.detailed_category = detailed

    cats = [
        DummyCat(1, None, "Food"),
        DummyCat(2, 1, "Food", "Groceries"),
        DummyCat(3, None, "Transport"),
    ]

    tx1 = DummyTransaction()
    tx1.amount = -30
    tx1.category_id = 2
    tx1.date = datetime.now().date()
    tx2 = DummyTransaction()
    tx2.amount = -50
    tx2.category_id = 3
    tx2.date = datetime.now().date()
    txs = [tx1, tx2]

    accounts = [DummyAccount(0, "checking")]

    def query(model, *a, **k):
        if model is charts_module.Category:
            return QueryStub(cats)
        if model is charts_module.Transaction:
            return QueryStub(txs)
        if model is charts_module.Account:
            return QueryStub(accounts)
        return QueryStub([])

    extensions_stub.db.session = types.SimpleNamespace(query=query)

    class DummyField:
        def __ge__(self, other):
            return True

        def __le__(self, other):
            return True

        def in_(self, other):
            return True

        def __eq__(self, other):
            return True

    dummy_field = DummyField()
    charts_module.Transaction.date = dummy_field
    charts_module.Transaction.category_id = dummy_field

    resp = client.get("/api/charts/category_breakdown_tree")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    root_total = sum(node["amount"] for node in data["data"])
    expected_total = sum(abs(t.amount) for t in txs)
    assert root_total == expected_total


def test_category_tree_shape_has_ids(client):
    class DummyCat:
        def __init__(self, id_, primary, detailed=None):
            self.id = id_
            self.primary_category = primary
            self.detailed_category = detailed
            self.display_name = detailed or primary
            self.plaid_category_id = f"plaid-{id_}"

    cats = [
        DummyCat(1, "Food"),
        DummyCat(2, "Food", "Groceries"),
        DummyCat(3, "Transport"),
    ]

    models_stub.Category.query = types.SimpleNamespace(all=lambda: cats)

    resp = client.get("/api/categories/tree")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert isinstance(data["data"], list)
    first = data["data"][0]
    assert set(first.keys()) == {"id", "label", "children"}
    assert all("label" in child for child in first["children"])
