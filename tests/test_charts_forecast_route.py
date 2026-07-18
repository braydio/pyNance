"""Tests for charts forecast route method safety."""

from __future__ import annotations

import importlib.util
import os
import sys
import types
from datetime import date

from flask import Flask

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHARTS_PATH = os.path.join(BASE_DIR, "backend", "app", "routes", "charts.py")


def _load_charts_module():
    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = []
    sys.modules.setdefault("app", app_pkg)

    config_stub = types.ModuleType("app.config")

    class _Logger:
        def debug(self, *_args, **_kwargs):
            return None

        def info(self, *_args, **_kwargs):
            return None

        def warning(self, *_args, **_kwargs):
            return None

        def error(self, *_args, **_kwargs):
            return None

    config_stub.logger = _Logger()
    sys.modules["app.config"] = config_stub

    extensions_stub = types.ModuleType("app.extensions")
    extensions_stub.db = types.SimpleNamespace(session=None)
    sys.modules["app.extensions"] = extensions_stub

    services_pkg = types.ModuleType("app.services")
    services_pkg.__path__ = []
    sys.modules["app.services"] = services_pkg

    orchestrator_stub = types.ModuleType("app.services.forecast_orchestrator")

    class _ForecastOrchestrator:
        def __init__(self, *_args, **_kwargs):
            pass

        def forecast(self, days=30):
            return []

    orchestrator_stub.ForecastOrchestrator = _ForecastOrchestrator
    sys.modules["app.services.forecast_orchestrator"] = orchestrator_stub

    utils_pkg = types.ModuleType("app.utils")
    utils_pkg.__path__ = []
    sys.modules["app.utils"] = utils_pkg

    finance_utils_stub = types.ModuleType("app.utils.finance_utils")
    finance_utils_stub.display_transaction_amount = lambda tx: 0
    finance_utils_stub.normalize_account_balance = lambda balance, *_args, **_kwargs: balance
    sys.modules["app.utils.finance_utils"] = finance_utils_stub

    sqlalchemy_stub = types.ModuleType("sqlalchemy")
    sqlalchemy_stub.case = lambda *args, **kwargs: None
    sqlalchemy_stub.func = types.SimpleNamespace(
        coalesce=lambda *args, **kwargs: None,
        sum=lambda *args, **kwargs: None,
        abs=lambda *args, **kwargs: None,
        count=lambda *args, **kwargs: None,
        strftime=lambda *args, **kwargs: None,
    )
    sys.modules["sqlalchemy"] = sqlalchemy_stub

    models_stub = types.ModuleType("app.models")

    class _QueryAttr:
        def in_(self, _value):
            return self

        def is_(self, _value):
            return self

        def __ge__(self, _value):
            return self

        def __le__(self, _value):
            return self

        def __lt__(self, _value):
            return self

        def __gt__(self, _value):
            return self

        def __or__(self, _other):
            return self

        def __eq__(self, _other):
            return self

        def desc(self):
            return self

    class _Account:
        account_id = _QueryAttr()
        is_hidden = _QueryAttr()
        user_id = _QueryAttr()
        balance = _QueryAttr()

    class _Category:
        id = _QueryAttr()

    class _Tag:
        id = _QueryAttr()
        name = _QueryAttr()

    class _Transaction:
        id = _QueryAttr()
        transaction_id = _QueryAttr()
        category_id = _QueryAttr()
        account_id = _QueryAttr()
        date = _QueryAttr()
        amount = _QueryAttr()
        is_internal = _QueryAttr()

    models_stub.Account = _Account
    models_stub.Category = _Category
    models_stub.Tag = _Tag
    models_stub.Transaction = _Transaction
    models_stub.transaction_tags = types.SimpleNamespace(
        c=types.SimpleNamespace(transaction_id=_QueryAttr(), tag_id=_QueryAttr())
    )
    sys.modules["app.models"] = models_stub

    spec = importlib.util.spec_from_file_location("app.routes.charts", CHARTS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_charts_forecast_rejects_post_method():
    charts_module = _load_charts_module()
    app = Flask(__name__)
    app.register_blueprint(charts_module.charts, url_prefix="/charts")

    with app.test_client() as client:
        response = client.post("/charts/forecast")

    assert response.status_code == 405


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def join(self, *_args, **_kwargs):
        return self

    def outerjoin(self, *_args, **_kwargs):
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.rows


def _transaction_row(transaction_id, amount, merchant_name="Store"):
    transaction = types.SimpleNamespace(
        transaction_id=transaction_id,
        date=date(2026, 7, 16),
        display_amount=amount,
        description=f"{merchant_name} purchase",
        merchant_name=merchant_name,
        category="Food",
        pending=False,
    )
    account = types.SimpleNamespace(
        name="Checking",
        institution_name="Example Bank",
        subtype="checking",
        account_id="account-1",
    )
    category = types.SimpleNamespace(pfc_icon_url=None)
    return transaction, account, category


def _drilldown_client(rows):
    charts_module = _load_charts_module()
    charts_module.db.session = types.SimpleNamespace(query=lambda *_args: _FakeQuery(rows))
    charts_module.display_transaction_amount = lambda transaction: transaction.display_amount
    app = Flask(__name__)
    app.register_blueprint(charts_module.charts, url_prefix="/charts")
    return app.test_client()


def test_category_transactions_returns_only_chart_expenses_for_full_requested_day():
    client = _drilldown_client([_transaction_row("expense", -12.5), _transaction_row("income", 20)])

    response = client.get("/charts/category_transactions?category_ids=10,20&start_date=2026-07-16&end_date=2026-07-16")

    assert response.status_code == 200
    transactions = response.get_json()["data"]["transactions"]
    assert [transaction["transaction_id"] for transaction in transactions] == ["expense"]
    assert transactions[0]["date"] == "2026-07-16"


def test_category_transactions_requires_valid_category_ids():
    client = _drilldown_client([])

    assert client.get("/charts/category_transactions").status_code == 400
    assert client.get("/charts/category_transactions?category_ids=not-a-number").status_code == 400


def test_merchant_transactions_matches_chart_label_and_excludes_income():
    client = _drilldown_client(
        [
            _transaction_row("coffee-expense", -8.25, "Coffee Shop"),
            _transaction_row("coffee-income", 15, "Coffee Shop"),
            _transaction_row("other-expense", -4, "Other Store"),
        ]
    )

    response = client.get(
        "/charts/merchant_transactions?merchant=Coffee%20Shop&start_date=2026-07-16&end_date=2026-07-16"
    )

    assert response.status_code == 200
    transactions = response.get_json()["data"]["transactions"]
    assert [transaction["transaction_id"] for transaction in transactions] == ["coffee-expense"]
