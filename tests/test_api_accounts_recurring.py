import importlib.util
import os
import sys
import types
from datetime import date, datetime
from pathlib import Path

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)
app_pkg = types.ModuleType("app")
app_pkg.__path__ = []
sys.modules["app"] = app_pkg
sys.modules["flask_cors"] = types.SimpleNamespace(CORS=lambda app: app)
sys.modules["flask_migrate"] = types.SimpleNamespace(Migrate=lambda *a, **k: None)

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FLASK_ENV = "test"
config_stub.plaid_client = None
config_stub.FILES = {
    "LAST_TX_REFRESH": "tx.json",
    "PLAID_TOKENS": "tokens.json",
}
config_stub.DIRECTORIES = {
    "DATA_DIR": Path("/tmp"),
}
sys.modules["app.config"] = config_stub

env_stub = types.ModuleType("app.config.environment")
sys.modules["app.config.environment"] = env_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace()
sys.modules["app.extensions"] = extensions_stub

utils_pkg = types.ModuleType("app.utils")
finance_stub = types.ModuleType("app.utils.finance_utils")
finance_stub.display_transaction_amount = lambda txn: (
    -txn.amount if getattr(txn, "transaction_type", "") == "expense" else txn.amount
)
finance_stub.normalize_account_balance = lambda b: b
sys.modules["app.utils"] = utils_pkg
sys.modules["app.utils.finance_utils"] = finance_stub

models_stub = types.ModuleType("app.models")
models_stub.Account = type("Account", (), {})
models_stub.Account.account_id = type("_Col", (), {"in_": lambda self, values: None})()
models_stub.PlaidAccount = type("PlaidAccount", (), {})
models_stub.PlaidItem = type("PlaidItem", (), {})
models_stub.PlaidItem.query = types.SimpleNamespace(
    filter_by=lambda **_: types.SimpleNamespace(all=lambda: [])
)
models_stub.RecurringTransaction = type("RecurringTransaction", (), {})
models_stub.Transaction = type("Transaction", (), {})
models_stub.AccountHistory = type("AccountHistory", (), {})
sys.modules["app.models"] = models_stub

sql_pkg = types.ModuleType("app.sql")
sql_pkg.account_logic = types.SimpleNamespace(
    refresh_data_for_plaid_account=lambda *args, **kwargs: (False, None),
)
sql_pkg.investments_logic = types.SimpleNamespace(
    upsert_investments_from_plaid=lambda *args, **kwargs: {
        "securities": 0,
        "holdings": 0,
    },
    upsert_investment_transactions=lambda *args, **kwargs: 0,
)
sys.modules["app.sql"] = sql_pkg

forecast_stub = types.ModuleType("app.sql.forecast_logic")
forecast_stub.update_account_history = lambda *args, **kwargs: None
sys.modules["app.sql.forecast_logic"] = forecast_stub

ROUTE_PATH = os.path.join(BASE_BACKEND, "app", "routes", "accounts.py")
spec = importlib.util.spec_from_file_location("app.routes.accounts", ROUTE_PATH)
accounts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounts_module)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(accounts_module.accounts, url_prefix="/api/accounts")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_recurring_uses_display_amount(client, monkeypatch):
    mock_tx = types.SimpleNamespace(
        id=1,
        description="Bill",
        frequency="monthly",
        next_due_date=date(2024, 1, 1),
        notes="",
        updated_at=datetime(2024, 1, 1),
        transaction=types.SimpleNamespace(amount=10.0, transaction_type="expense"),
    )
    query = types.SimpleNamespace(
        filter_by=lambda **kwargs: types.SimpleNamespace(all=lambda: [mock_tx])
    )
    monkeypatch.setattr(
        accounts_module.RecurringTransaction, "query", query, raising=False
    )

    resp = client.get("/api/accounts/acc1/recurring")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["reminders"][0]["amount"] == -10.0


def test_refresh_single_account_investments_product(client, monkeypatch):
    account = types.SimpleNamespace(
        account_id="acct-invest",
        account_id_int=1,
        link_type="Plaid",
        user_id="user-1",
        name="Investing",
        institution_name="MockBank",
        plaid_account=types.SimpleNamespace(
            access_token="token-123",
            product="investments",
            item_id="item-1",
        ),
    )

    monkeypatch.setattr(
        accounts_module.Account,
        "query",
        types.SimpleNamespace(
            filter_by=lambda **_: types.SimpleNamespace(first=lambda: account)
        ),
        raising=False,
    )

    calls = {}

    def fake_refresh(*_, **__):
        raise AssertionError("Transactions refresh should not be invoked")

    monkeypatch.setattr(
        sql_pkg.account_logic,
        "refresh_data_for_plaid_account",
        fake_refresh,
    )

    def fake_investments(acct, token, start_date=None, end_date=None):
        calls["account"] = acct
        calls["token"] = token
        calls["start"] = start_date
        calls["end"] = end_date
        return True

    monkeypatch.setattr(
        accounts_module,
        "_refresh_plaid_investments",
        fake_investments,
    )

    monkeypatch.setattr(
        accounts_module.db,
        "session",
        types.SimpleNamespace(commit=lambda: None, rollback=lambda: None),
        raising=False,
    )

    resp = client.post(
        "/api/accounts/acct-invest/refresh",
        json={"start_date": "2024-01-01", "end_date": "2024-01-31"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["updated"] is True
    assert calls["account"] is account
    assert calls["token"] == "token-123"
    assert calls["start"] == "2024-01-01"
    assert calls["end"] == "2024-01-31"


def test_refresh_all_accounts_handles_investments_only(client, monkeypatch):
    account = types.SimpleNamespace(
        account_id="acct-invest",
        link_type="Plaid",
        user_id="user-1",
        name="Investing",
        institution_name="MockBank",
        plaid_account=types.SimpleNamespace(
            access_token="token-abc",
            product="investments",
            item_id="item-2",
        ),
    )

    class QueryStub:
        def __init__(self, records):
            self._records = records

        def filter(self, *_args, **_kwargs):
            return QueryStub(self._records)

        def filter_by(self, **_kwargs):
            return QueryStub(self._records)

        def all(self):
            return list(self._records)

    monkeypatch.setattr(
        accounts_module.Account, "query", QueryStub([account]), raising=False
    )

    def fail_transactions(*_args, **_kwargs):
        raise AssertionError("Transactions refresh should be skipped")

    monkeypatch.setattr(
        sql_pkg.account_logic,
        "refresh_data_for_plaid_account",
        fail_transactions,
    )

    investment_calls = {}

    def fake_investments(acct, token, start_date=None, end_date=None):
        investment_calls.setdefault("accounts", []).append(acct)
        investment_calls.setdefault("token", token)
        investment_calls.setdefault("start", start_date)
        investment_calls.setdefault("end", end_date)
        return True

    monkeypatch.setattr(
        accounts_module,
        "_refresh_plaid_investments",
        fake_investments,
    )

    monkeypatch.setattr(
        accounts_module,
        "load_tokens",
        lambda: [],
        raising=False,
    )

    monkeypatch.setattr(
        accounts_module.db,
        "session",
        types.SimpleNamespace(commit=lambda: None, rollback=lambda: None),
        raising=False,
    )

    resp = client.post(
        "/api/accounts/refresh_accounts",
        json={
            "account_ids": ["acct-invest"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )
    assert resp.status_code == 200, resp.get_json()
    payload = resp.get_json()
    assert payload["status"] == "success"
    assert payload["updated_accounts"] == ["Investing"]
    assert payload["refreshed_counts"] == {"MockBank": 1}
    assert investment_calls.get("accounts") == [account]
    assert investment_calls.get("token") == "token-abc"
    assert investment_calls.get("start") == "2024-01-01"
    assert investment_calls.get("end") == "2024-01-31"
