"""Tests for transaction-related API routes."""

import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest
from flask import Flask

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
config_stub.DIRECTORIES = {
    "CERTS_DIR": Path("/tmp"),
    "DATA_DIR": Path("/tmp"),
}
config_stub.FLASK_ENV = "test"
sys.modules["app.config"] = config_stub

env_stub = types.ModuleType("app.config.environment")
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

# SQL package and logic
sql_pkg = types.ModuleType("app.sql")
account_logic_stub = types.ModuleType("app.sql.account_logic")
account_logic_stub.get_paginated_transactions = lambda *a, **k: ([{"id": "t1"}], 1, {})
account_logic_stub.invalidate_tx_cache = lambda: None
sys.modules["app.sql"] = sql_pkg
sys.modules["app.sql.account_logic"] = account_logic_stub
sql_pkg.account_logic = account_logic_stub

models_stub = types.ModuleType("app.models")
models_stub.Account = type("Account", (), {})
models_stub.Category = type("Category", (), {})
models_stub.Tag = type("Tag", (), {})
models_stub.Transaction = type("Transaction", (), {})
models_stub.AccountHistory = type("AccountHistory", (), {})
sys.modules["app.models"] = models_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "transactions.py")
spec = importlib.util.spec_from_file_location("app.routes.transactions", ROUTE_PATH)
transactions_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transactions_module)


class _Expr:
    def is_(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def __or__(self, _other):
        return self

    def __ge__(self, _other):
        return self

    def __le__(self, _other):
        return self

    def __eq__(self, _other):
        return self


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(
        transactions_module.transactions, url_prefix="/api/transactions"
    )
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_transactions_returns_data(client, monkeypatch):
    monkeypatch.setattr(
        transactions_module.account_logic,
        "get_paginated_transactions",
        lambda *a, **k: ([{"txn": 1, "category_icon_url": "url"}], 1, {}),
    )
    resp = client.get("/api/transactions/get_transactions")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["data"]["transactions"] == [{"txn": 1, "category_icon_url": "url"}]
    assert data["data"]["total"] == 1


def test_account_transactions_recent_limited_and_sorted(client, monkeypatch):
    """Verify recent transactions are limited and sorted by date."""
    sample = [
        {"transaction_id": "t1", "date": "2024-02-01"},
        {"transaction_id": "t2", "date": "2024-01-15"},
        {"transaction_id": "t3", "date": "2024-01-01"},
    ]
    captured = {}

    def fake_get_paginated(
        page,
        page_size,
        start_date=None,
        end_date=None,
        category=None,
        user_id=None,
        account_id=None,
        account_ids=None,
        recent=False,
        limit=None,
        tags=None,
        tx_type=None,
        transaction_id=None,
        include_running_balance=False,
    ):
        captured["recent"] = recent
        captured["limit"] = limit
        ordered = sorted(sample, key=lambda x: x["date"], reverse=True)
        return ordered[: (limit or page_size)], len(sample), {}

    monkeypatch.setattr(
        transactions_module.account_logic,
        "get_paginated_transactions",
        fake_get_paginated,
    )
    resp = client.get("/api/transactions/acc1/transactions?recent=true&limit=2")
    assert resp.status_code == 200
    data = resp.get_json()
    ids = [t["transaction_id"] for t in data["data"]["transactions"]]
    assert ids == ["t1", "t2"]
    assert len(ids) == 2
    assert captured["recent"] is True
    assert captured["limit"] == 2


def test_get_transactions_accepts_tag_filters(client, monkeypatch):
    captured = {}

    def fake_get_paginated(*_args, **kwargs):
        captured["tags"] = kwargs.get("tags")
        return ([{"txn": 1}], 1, {})

    monkeypatch.setattr(
        transactions_module.account_logic,
        "get_paginated_transactions",
        fake_get_paginated,
    )

    resp = client.get("/api/transactions/get_transactions?tag=coffee")
    assert resp.status_code == 200
    assert captured["tags"] == ["#coffee", "coffee"]


def test_update_transaction_validates_date(client, monkeypatch):
    txn_stub = types.SimpleNamespace(
        amount=0.0,
        date=None,
        description="",
        category="",
        merchant_name="",
        merchant_type="",
        is_internal=False,
        user_id="user-1",
        user_modified=False,
        user_modified_fields=None,
    )
    query_result = types.SimpleNamespace(first=lambda: txn_stub)
    monkeypatch.setattr(
        transactions_module.Transaction,
        "query",
        types.SimpleNamespace(filter_by=lambda **kwargs: query_result),
        raising=False,
    )
    monkeypatch.setattr(
        transactions_module,
        "db",
        types.SimpleNamespace(session=types.SimpleNamespace(commit=lambda: None)),
        raising=False,
    )

    resp = client.put(
        "/api/transactions/update",
        json={"transaction_id": "tx1", "date": "bad-date"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["status"] == "error"

    resp = client.put(
        "/api/transactions/update",
        json={"transaction_id": "tx1", "date": "2024-01-02"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"


def test_update_transaction_applies_tag_normalization(client, monkeypatch):
    added_tags = []

    class TagStub:
        def __init__(self, user_id, name):
            self.user_id = user_id
            self.name = name

    def tag_filter_by(user_id=None, name=None):
        return types.SimpleNamespace(first=lambda: None)

    txn_stub = types.SimpleNamespace(
        amount=0.0,
        date=None,
        description="",
        category="",
        merchant_name="",
        merchant_type="",
        is_internal=False,
        user_id="user-1",
        user_modified=False,
        user_modified_fields=None,
        tags=[],
    )
    query_result = types.SimpleNamespace(first=lambda: txn_stub)
    monkeypatch.setattr(
        transactions_module.Transaction,
        "query",
        types.SimpleNamespace(filter_by=lambda **kwargs: query_result),
        raising=False,
    )
    TagStub.query = types.SimpleNamespace(filter_by=tag_filter_by)
    monkeypatch.setattr(transactions_module, "Tag", TagStub, raising=False)
    monkeypatch.setattr(
        transactions_module,
        "db",
        types.SimpleNamespace(
            session=types.SimpleNamespace(add=added_tags.append, commit=lambda: None)
        ),
        raising=False,
    )

    resp = client.put(
        "/api/transactions/update",
        json={"transaction_id": "tx1", "tag": "  coffee  "},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"
    assert txn_stub.tags[0].name == "#coffee"
    assert added_tags[0].name == "#coffee"


def test_update_transaction_defaults_empty_tag(client, monkeypatch):
    added_tags = []

    class TagStub:
        def __init__(self, user_id, name):
            self.user_id = user_id
            self.name = name

    def tag_filter_by(user_id=None, name=None):
        return types.SimpleNamespace(first=lambda: None)

    txn_stub = types.SimpleNamespace(
        amount=0.0,
        date=None,
        description="",
        category="",
        merchant_name="",
        merchant_type="",
        is_internal=False,
        user_id="user-1",
        user_modified=False,
        user_modified_fields=None,
        tags=[],
    )
    query_result = types.SimpleNamespace(first=lambda: txn_stub)
    monkeypatch.setattr(
        transactions_module.Transaction,
        "query",
        types.SimpleNamespace(filter_by=lambda **kwargs: query_result),
        raising=False,
    )
    TagStub.query = types.SimpleNamespace(filter_by=tag_filter_by)
    monkeypatch.setattr(transactions_module, "Tag", TagStub, raising=False)
    monkeypatch.setattr(
        transactions_module,
        "db",
        types.SimpleNamespace(
            session=types.SimpleNamespace(add=added_tags.append, commit=lambda: None)
        ),
        raising=False,
    )

    resp = client.put(
        "/api/transactions/update",
        json={"transaction_id": "tx1", "tag": "   "},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"
    assert txn_stub.tags[0].name == "#untagged"
    assert added_tags[0].name == "#untagged"


def test_top_merchants_returns_frontend_shape(client, monkeypatch):
    rows = [
        (
            types.SimpleNamespace(
                amount=10,
                date=transactions_module.datetime(
                    2026, 2, 5, tzinfo=transactions_module.UTC
                ),
                merchant_name="Coffee Shop",
                merchant_slug="coffee-shop",
                description="Coffee",
                category="Food",
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            None,
        ),
        (
            types.SimpleNamespace(
                amount=15,
                date=transactions_module.datetime(
                    2026, 1, 10, tzinfo=transactions_module.UTC
                ),
                merchant_name="Coffee Shop",
                merchant_slug="coffee-shop",
                description="Coffee",
                category="Food",
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            None,
        ),
        (
            types.SimpleNamespace(
                amount=20,
                date=transactions_module.datetime(
                    2026, 2, 3, tzinfo=transactions_module.UTC
                ),
                merchant_name="Grocery Mart",
                merchant_slug="grocery-mart",
                description="Groceries",
                category="Groceries",
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            None,
        ),
    ]

    class QueryStub:
        def join(self, *_args, **_kwargs):
            return self

        def outerjoin(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def all(self):
            return rows

    monkeypatch.setattr(
        transactions_module,
        "db",
        types.SimpleNamespace(
            session=types.SimpleNamespace(query=lambda *_args, **_kwargs: QueryStub())
        ),
        raising=False,
    )
    monkeypatch.setattr(
        transactions_module.Account, "is_hidden", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "is_internal", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "pending", _Expr(), raising=False
    )
    monkeypatch.setattr(transactions_module.Transaction, "date", _Expr(), raising=False)
    monkeypatch.setattr(
        transactions_module.Transaction, "account_id", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "category_id", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Account, "account_id", _Expr(), raising=False
    )
    monkeypatch.setattr(transactions_module.Category, "id", _Expr(), raising=False)
    monkeypatch.setattr(
        transactions_module, "display_transaction_amount", lambda txn: -abs(txn.amount)
    )

    resp = client.get("/api/transactions/top_merchants?trend_points=3")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["data"][0]["name"] == "Coffee Shop"
    assert data["data"][0]["total"] == 25.0
    assert len(data["data"][0]["trend"]) == 3


def test_top_categories_uses_category_fallback_and_top_n(client, monkeypatch):
    rows = [
        (
            types.SimpleNamespace(
                amount=30,
                date=transactions_module.datetime(
                    2026, 2, 1, tzinfo=transactions_module.UTC
                ),
                merchant_name="A",
                merchant_slug="a",
                description="A",
                category="",
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            types.SimpleNamespace(computed_display_name="Bills - Utilities"),
        ),
        (
            types.SimpleNamespace(
                amount=10,
                date=transactions_module.datetime(
                    2026, 2, 2, tzinfo=transactions_module.UTC
                ),
                merchant_name="B",
                merchant_slug="b",
                description="B",
                category="Dining",
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            types.SimpleNamespace(computed_display_name="Ignored"),
        ),
    ]

    class QueryStub:
        def join(self, *_args, **_kwargs):
            return self

        def outerjoin(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def all(self):
            return rows

    monkeypatch.setattr(
        transactions_module,
        "db",
        types.SimpleNamespace(
            session=types.SimpleNamespace(query=lambda *_args, **_kwargs: QueryStub())
        ),
        raising=False,
    )
    monkeypatch.setattr(
        transactions_module.Account, "is_hidden", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "is_internal", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "pending", _Expr(), raising=False
    )
    monkeypatch.setattr(transactions_module.Transaction, "date", _Expr(), raising=False)
    monkeypatch.setattr(
        transactions_module.Transaction, "account_id", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "category_id", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Account, "account_id", _Expr(), raising=False
    )
    monkeypatch.setattr(transactions_module.Category, "id", _Expr(), raising=False)
    monkeypatch.setattr(
        transactions_module, "display_transaction_amount", lambda txn: -abs(txn.amount)
    )

    resp = client.get("/api/transactions/top_categories?top_n=1&trend_points=4")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Bills - Utilities"
    assert data["data"][0]["total"] == 30.0
    assert len(data["data"][0]["trend"]) == 4


def test_top_merchants_groups_by_canonical_slug(client, monkeypatch):
    rows = [
        (
            types.SimpleNamespace(
                amount=12,
                date=transactions_module.datetime(
                    2026, 2, 5, tzinfo=transactions_module.UTC
                ),
                merchant_name="Joe's Coffee",
                merchant_slug="joes-coffee",
                description="POS JOE'S COFFEE #123",
                category="Food",
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            None,
        ),
        (
            types.SimpleNamespace(
                amount=8,
                date=transactions_module.datetime(
                    2026, 2, 10, tzinfo=transactions_module.UTC
                ),
                merchant_name="Joes Coffee",
                merchant_slug="joes-coffee",
                description="DEBIT JOES COFFEE",
                category="Food",
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            None,
        ),
    ]

    class QueryStub:
        def join(self, *_args, **_kwargs):
            return self

        def outerjoin(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def all(self):
            return rows

    monkeypatch.setattr(
        transactions_module,
        "db",
        types.SimpleNamespace(
            session=types.SimpleNamespace(query=lambda *_args, **_kwargs: QueryStub())
        ),
        raising=False,
    )
    monkeypatch.setattr(
        transactions_module.Account, "is_hidden", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "is_internal", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "pending", _Expr(), raising=False
    )
    monkeypatch.setattr(transactions_module.Transaction, "date", _Expr(), raising=False)
    monkeypatch.setattr(
        transactions_module.Transaction, "account_id", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "category_id", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Account, "account_id", _Expr(), raising=False
    )
    monkeypatch.setattr(transactions_module.Category, "id", _Expr(), raising=False)
    monkeypatch.setattr(
        transactions_module, "display_transaction_amount", lambda txn: -abs(txn.amount)
    )

    resp = client.get("/api/transactions/top_merchants?trend_points=3")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] == "success"
    assert len(payload["data"]) == 1
    assert payload["data"][0]["name"] == "Joe's Coffee"
    assert payload["data"][0]["total"] == 20.0


def test_top_categories_groups_equivalent_variants_without_slug(client, monkeypatch):
    rows = [
        (
            types.SimpleNamespace(
                amount=9,
                date=transactions_module.datetime(
                    2026, 2, 1, tzinfo=transactions_module.UTC
                ),
                merchant_name="Shop A",
                merchant_slug="shop-a",
                description="A",
                category="Food & Drink: Coffee",
                category_slug=None,
                category_display=None,
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            None,
        ),
        (
            types.SimpleNamespace(
                amount=11,
                date=transactions_module.datetime(
                    2026, 2, 2, tzinfo=transactions_module.UTC
                ),
                merchant_name="Shop B",
                merchant_slug="shop-b",
                description="B",
                category="Food and Drink Coffee",
                category_slug=None,
                category_display=None,
                pending=False,
                is_internal=False,
            ),
            types.SimpleNamespace(),
            None,
        ),
    ]

    class QueryStub:
        def join(self, *_args, **_kwargs):
            return self

        def outerjoin(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def all(self):
            return rows

    monkeypatch.setattr(
        transactions_module,
        "db",
        types.SimpleNamespace(
            session=types.SimpleNamespace(query=lambda *_args, **_kwargs: QueryStub())
        ),
        raising=False,
    )
    monkeypatch.setattr(
        transactions_module.Account, "is_hidden", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "is_internal", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "pending", _Expr(), raising=False
    )
    monkeypatch.setattr(transactions_module.Transaction, "date", _Expr(), raising=False)
    monkeypatch.setattr(
        transactions_module.Transaction, "account_id", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Transaction, "category_id", _Expr(), raising=False
    )
    monkeypatch.setattr(
        transactions_module.Account, "account_id", _Expr(), raising=False
    )
    monkeypatch.setattr(transactions_module.Category, "id", _Expr(), raising=False)
    monkeypatch.setattr(
        transactions_module, "display_transaction_amount", lambda txn: -abs(txn.amount)
    )

    resp = client.get("/api/transactions/top_categories?trend_points=3")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] == "success"
    assert len(payload["data"]) == 1
    assert payload["data"][0]["slug"] == "FOOD_AND_DRINK_COFFEE"
    assert payload["data"][0]["name"] == "Food & Drink: Coffee"
    assert payload["data"][0]["total"] == 20.0
