"""Tests for canonical Plaid product scope parsing in accounts routes."""

import importlib.util
import json
import os
import sys
import types

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")

sys.modules.pop("app.sql.account_logic", None)
sys.modules.pop("app.config", None)
sys.modules.pop("app.models", None)


# Stub app.config
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.DB_IDENTITY = None
config_stub.DB_SCHEMA = None
config_stub.IS_DEV = False
config_stub.IS_TEST = True
config_stub.plaid_client = None
sys.modules["app.config"] = config_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

models_stub = types.ModuleType("app.models")


class DummyAccount:
    pass


class DummyPlaidItem:
    _items = []


class _DummyPlaidItemQuery:
    def filter_by(self, **kwargs):
        item_id = kwargs.get("item_id")
        matched = [
            i for i in DummyPlaidItem._items if getattr(i, "item_id", None) == item_id
        ]
        return types.SimpleNamespace(all=lambda: matched)


DummyPlaidItem.query = _DummyPlaidItemQuery()
models_stub.Account = DummyAccount
models_stub.PlaidItem = DummyPlaidItem
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
models_stub.Transaction = type("Transaction", (), {})
sys.modules["app.models"] = models_stub

svc_stub = types.ModuleType("app.services.accounts_service")
svc_stub.fetch_accounts = lambda *a, **k: []
sys.modules["app.services.accounts_service"] = svc_stub

logic_stub = types.ModuleType("app.sql.account_logic")


def _canonicalize(value):
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return _canonicalize(parsed)
        values = raw.split(",")
    elif isinstance(value, (list, set, tuple)):
        values = list(value)
    else:
        values = [value]
    return sorted({str(part).strip() for part in values if str(part).strip()})


logic_stub.canonicalize_plaid_products = _canonicalize
logic_stub.refresh_is_stale = lambda *_a, **_k: False
logic_stub.serialized_refresh_status = lambda *_a, **_k: {}
logic_stub.should_throttle_refresh = lambda *_a, **_k: False
sys.modules["app.sql.account_logic"] = logic_stub

forecast_stub = types.ModuleType("app.sql.forecast_logic")
forecast_stub.update_account_history = lambda *_a, **_k: None
sys.modules["app.sql.forecast_logic"] = forecast_stub

finance_stub = types.ModuleType("app.utils.finance_utils")
finance_stub.display_transaction_amount = lambda *_a, **_k: 0
finance_stub.normalize_account_balance = lambda balance, *_a, **_k: balance
sys.modules["app.utils.finance_utils"] = finance_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "accounts.py")
spec = importlib.util.spec_from_file_location(
    "tests._accounts_route_scopes", ROUTE_PATH
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_normalize_products_accepts_json_and_csv_formats():
    assert module._normalize_products("transactions,investments") == {
        "transactions",
        "investments",
    }
    assert module._normalize_products('["investments", "transactions"]') == {
        "transactions",
        "investments",
    }


def test_plaid_products_for_account_unions_item_and_account_scopes():
    plaid_account = types.SimpleNamespace(product="transactions", item_id="item-1")
    account = types.SimpleNamespace(plaid_account=plaid_account)

    item = types.SimpleNamespace(item_id="item-1", product="investments")
    DummyPlaidItem._items = [item]

    assert module._plaid_products_for_account(account) == {
        "transactions",
        "investments",
    }
