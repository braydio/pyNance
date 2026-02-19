"""Tests for charts forecast route method safety."""

from __future__ import annotations

import importlib.util
import os
import sys
import types

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
    finance_utils_stub.normalize_account_balance = (
        lambda balance, *_args, **_kwargs: balance
    )
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
