"""Route tests for investments, Plaid investments, and Plaid webhook flows."""

import importlib.util
import os
import sys
import types
from dataclasses import dataclass
from datetime import date

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")


class FilterColumn:
    """Simple descriptor that can generate predicate callables for query stubs."""

    def __init__(self, attr: str):
        self.attr = attr

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.attr)

    def __set__(self, instance, value):
        setattr(instance, self.attr, value)

    def __eq__(self, other):
        return lambda row: getattr(row, self.attr) == other

    def __ge__(self, other):
        return lambda row: getattr(row, self.attr) >= other

    def __le__(self, other):
        return lambda row: getattr(row, self.attr) <= other

    def desc(self):
        return ("desc", self.attr)


class QueryListStub:
    """In-memory query object with common SQLAlchemy-style operations."""

    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, predicate):
        self._rows = [row for row in self._rows if predicate(row)]
        return self

    def order_by(self, order):
        direction, attr = order
        self._rows = sorted(
            self._rows, key=lambda row: getattr(row, attr), reverse=direction == "desc"
        )
        return self

    def count(self):
        return len(self._rows)

    def offset(self, count):
        self._rows = self._rows[count:]
        return self

    def limit(self, count):
        self._rows = self._rows[:count]
        return self

    def all(self):
        return list(self._rows)


@dataclass
class Txn:
    investment_transaction_id: str
    account_id: str
    security_id: str
    date: date
    amount: float
    price: float
    quantity: float
    subtype: str
    type: str
    name: str
    fees: float
    iso_currency_code: str


@dataclass
class Holding:
    account_id: str
    security_id: str
    quantity: float
    cost_basis: float
    institution_value: float
    as_of: date


@dataclass
class Sec:
    security_id: str
    name: str
    ticker_symbol: str
    type: str
    iso_currency_code: str
    institution_price: float
    institution_price_as_of: date


class PlaidAccountStub:
    """Simple PlaidAccount stand-in for route tests."""

    query = None

    def __init__(
        self,
        account_id: str,
        item_id: str,
        access_token: str,
        product: str = "investments",
        is_active: bool = True,
        account=None,
    ):
        self.account_id = account_id
        self.item_id = item_id
        self.access_token = access_token
        self.product = product
        self.is_active = is_active
        self.account = account


class PlaidQueryStub:
    """Query helper for Plaid account collection filtering."""

    def __init__(self, rows):
        self.rows = list(rows)

    def filter_by(self, **kwargs):
        filtered = [
            row
            for row in self.rows
            if all(getattr(row, key, None) == value for key, value in kwargs.items())
        ]
        return PlaidQueryStub(filtered)

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return list(self.rows)


class WebhookLogStub:
    def __init__(self, **kwargs):
        self.payload = kwargs


def _load_module(
    module_name: str, route_path: str, models_stub, sql_pkg, helpers_stub=None
):
    """Load a backend route module with lightweight dependency stubs."""

    sys.path.insert(0, BASE_BACKEND)
    sys.modules.pop("app", None)

    config_stub = types.ModuleType("app.config")
    config_stub.logger = types.SimpleNamespace(
        info=lambda *a, **k: None,
        debug=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        error=lambda *a, **k: None,
    )
    config_stub.PLAID_WEBHOOK_SECRET = "secret"
    sys.modules["app.config"] = config_stub

    extensions_stub = types.ModuleType("app.extensions")
    extensions_stub.db = types.SimpleNamespace(
        session=types.SimpleNamespace(
            add=lambda *_: None, commit=lambda: None, rollback=lambda: None
        )
    )
    sys.modules["app.extensions"] = extensions_stub

    sys.modules["app.sql"] = sql_pkg
    sys.modules["app.models"] = models_stub

    if helpers_stub is not None:
        helpers_pkg = types.ModuleType("app.helpers")
        helpers_pkg.plaid_helpers = helpers_stub
        sys.modules["app.helpers"] = helpers_pkg
        sys.modules["app.helpers.plaid_helpers"] = helpers_stub

    spec = importlib.util.spec_from_file_location(module_name, route_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def investments_client():
    models_stub = types.ModuleType("app.models")
    models_stub.InvestmentHolding = type(
        "InvestmentHolding", (), {"security_id": FilterColumn("security_id")}
    )

    models_stub.InvestmentTransaction = type(
        "InvestmentTransaction",
        (),
        {
            "query": None,
            "account_id": FilterColumn("account_id"),
            "security_id": FilterColumn("security_id"),
            "type": FilterColumn("type"),
            "subtype": FilterColumn("subtype"),
            "date": FilterColumn("date"),
        },
    )
    models_stub.Security = type(
        "Security", (), {"security_id": FilterColumn("security_id")}
    )

    investments_logic_stub = types.ModuleType("app.sql.investments_logic")
    investments_logic_stub.get_investment_accounts = lambda: [{"account_id": "inv-1"}]

    sql_pkg = types.ModuleType("app.sql")
    sql_pkg.investments_logic = investments_logic_stub
    sys.modules["app.sql.investments_logic"] = investments_logic_stub

    module = _load_module(
        "app.routes.investments",
        os.path.join(BASE_BACKEND, "app", "routes", "investments.py"),
        models_stub,
        sql_pkg,
    )

    holding = Holding("acc-1", "sec-1", 2.0, 10.0, 30.0, date(2024, 5, 2))
    security = Sec(
        "sec-1", "Security One", "SEC1", "equity", "USD", 15.0, date(2024, 5, 2)
    )

    class SessionQuery:
        def join(self, *_args, **_kwargs):
            return self

        def all(self):
            return [(holding, security)]

    module.db = types.SimpleNamespace(
        session=types.SimpleNamespace(query=lambda *_: SessionQuery())
    )

    txns = [
        Txn(
            "t3",
            "acc-1",
            "sec-1",
            date(2024, 1, 3),
            30.0,
            3.0,
            10.0,
            "buy",
            "trade",
            "third",
            0.0,
            "USD",
        ),
        Txn(
            "t2",
            "acc-1",
            "sec-1",
            date(2024, 1, 2),
            20.0,
            2.0,
            10.0,
            "buy",
            "trade",
            "second",
            0.0,
            "USD",
        ),
        Txn(
            "t1",
            "acc-2",
            "sec-2",
            date(2024, 1, 1),
            10.0,
            1.0,
            10.0,
            "sell",
            "cash",
            "first",
            0.0,
            "USD",
        ),
    ]
    models_stub.InvestmentTransaction.query = QueryListStub(txns)

    app = Flask(__name__)
    app.register_blueprint(module.investments, url_prefix="/api/investments")
    with app.test_client() as client:
        yield client, module, models_stub, txns


def test_investments_success_endpoints(investments_client):
    client, _module, _models_stub, _txns = investments_client

    accounts_resp = client.get("/api/investments/accounts")
    holdings_resp = client.get("/api/investments/holdings")
    tx_resp = client.get("/api/investments/transactions")

    assert accounts_resp.status_code == 200
    assert holdings_resp.status_code == 200
    assert tx_resp.status_code == 200
    assert accounts_resp.get_json()["data"][0]["account_id"] == "inv-1"
    assert holdings_resp.get_json()["data"][0]["security"]["ticker_symbol"] == "SEC1"
    assert tx_resp.get_json()["data"]["total"] == 3


def test_investments_transactions_date_validation_errors(investments_client):
    client, *_ = investments_client

    bad_format = client.get("/api/investments/transactions?start_date=2024/01/01")
    reversed_range = client.get(
        "/api/investments/transactions?start_date=2024-02-02&end_date=2024-01-01"
    )

    assert bad_format.status_code == 400
    assert "Invalid date" in bad_format.get_json()["error"]
    assert reversed_range.status_code == 400
    assert (
        "end_date must be greater than or equal" in reversed_range.get_json()["error"]
    )


def test_investments_transactions_combined_filters_and_pagination(investments_client):
    client, _module, models_stub, txns = investments_client
    models_stub.InvestmentTransaction.query = QueryListStub(txns)

    resp = client.get(
        "/api/investments/transactions?account_id=acc-1&security_id=sec-1&type=trade&subtype=buy"
        "&start_date=2024-01-01&end_date=2024-01-03&page=1&page_size=1"
    )

    assert resp.status_code == 200
    payload = resp.get_json()["data"]
    assert payload["total"] == 2
    assert payload["filters"] == {
        "account_id": "acc-1",
        "security_id": "sec-1",
        "type": "trade",
        "subtype": "buy",
        "start_date": "2024-01-01",
        "end_date": "2024-01-03",
    }
    assert [txn["investment_transaction_id"] for txn in payload["transactions"]] == [
        "t3"
    ]


@pytest.fixture
def plaid_investments_client():
    models_stub = types.ModuleType("app.models")
    models_stub.PlaidAccount = PlaidAccountStub
    models_stub.PlaidItem = type(
        "PlaidItem",
        (),
        {
            "query": types.SimpleNamespace(
                filter_by=lambda **_k: types.SimpleNamespace(first=lambda: None)
            )
        },
    )

    investments_logic_stub = types.ModuleType("app.sql.investments_logic")
    investments_logic_stub.upsert_investments_from_plaid = lambda *_a, **_k: {
        "securities": 1,
        "holdings": 2,
    }
    investments_logic_stub.upsert_investment_transactions = lambda txs: len(txs)

    account_logic_stub = types.ModuleType("app.sql.account_logic")
    account_logic_stub.save_plaid_account = lambda *_a, **_k: None
    account_logic_stub.upsert_accounts = lambda *_a, **_k: None

    sql_pkg = types.ModuleType("app.sql")
    sql_pkg.investments_logic = investments_logic_stub
    sys.modules["app.sql.investments_logic"] = investments_logic_stub
    sys.modules["app.sql.account_logic"] = account_logic_stub

    helpers_stub = types.ModuleType("app.helpers.plaid_helpers")
    helpers_stub.exchange_public_token = lambda *_a, **_k: {
        "access_token": "token",
        "item_id": "item",
    }
    helpers_stub.generate_link_token = lambda *_a, **_k: "link-token"
    helpers_stub.get_accounts = lambda *_a, **_k: []
    helpers_stub.get_investment_transactions = lambda *_a, **_k: [
        {"id": "tx-1"},
        {"id": "tx-2"},
    ]

    module = _load_module(
        "app.routes.plaid_investments",
        os.path.join(BASE_BACKEND, "app", "routes", "plaid_investments.py"),
        models_stub,
        sql_pkg,
        helpers_stub=helpers_stub,
    )

    app = Flask(__name__)
    app.register_blueprint(
        module.plaid_investments, url_prefix="/api/plaid/investments"
    )
    with app.test_client() as client:
        yield client, module


def test_plaid_investments_input_validation(plaid_investments_client):
    client, _module = plaid_investments_client

    missing_user = client.post("/api/plaid/investments/generate_link_token", json={})
    missing_public_token = client.post(
        "/api/plaid/investments/exchange_public_token", json={"user_id": "u1"}
    )
    missing_item_id = client.post(
        "/api/plaid/investments/refresh", json={"user_id": "u1"}
    )

    assert missing_user.status_code == 400
    assert missing_public_token.status_code == 400
    assert missing_item_id.status_code == 400


def test_plaid_investments_refresh_success_path(plaid_investments_client, monkeypatch):
    client, module = plaid_investments_client

    account = PlaidAccountStub("acct-1", "item-1", "token-1")
    module.PlaidAccount.query = PlaidQueryStub([account])

    monkeypatch.setattr(
        module.investments_logic,
        "upsert_investments_from_plaid",
        lambda user_id, token: {"securities": 3, "holdings": 4},
    )
    monkeypatch.setattr(
        module,
        "get_investment_transactions",
        lambda token, start_date, end_date: [{"id": "a"}, {"id": "b"}],
    )
    monkeypatch.setattr(
        module.investments_logic, "upsert_investment_transactions", lambda txs: len(txs)
    )

    resp = client.post(
        "/api/plaid/investments/refresh",
        json={
            "user_id": "u1",
            "item_id": "item-1",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )

    assert resp.status_code == 200
    assert resp.get_json()["upserts"] == {
        "securities": 3,
        "holdings": 4,
        "investment_transactions": 2,
    }


def test_plaid_investments_refresh_all_aggregates_summary(
    plaid_investments_client, monkeypatch
):
    client, module = plaid_investments_client

    first = PlaidAccountStub(
        "acct-1", "item-1", "token-1", account=types.SimpleNamespace(user_id="u1")
    )
    second = PlaidAccountStub(
        "acct-2", "item-2", "token-2", account=types.SimpleNamespace(user_id="u2")
    )
    module.PlaidAccount.query = PlaidQueryStub([first, second])

    holdings_counts = {
        "token-1": {"securities": 1, "holdings": 2},
        "token-2": {"securities": 3, "holdings": 4},
    }
    tx_counts = {"token-1": [{"id": "x"}], "token-2": [{"id": "y"}, {"id": "z"}]}

    monkeypatch.setattr(
        module.investments_logic,
        "upsert_investments_from_plaid",
        lambda _user_id, token: holdings_counts[token],
    )
    monkeypatch.setattr(
        module,
        "get_investment_transactions",
        lambda token, _start, _end: tx_counts[token],
    )
    monkeypatch.setattr(
        module.investments_logic, "upsert_investment_transactions", lambda txs: len(txs)
    )

    resp = client.post(
        "/api/plaid/investments/refresh_all",
        json={"start_date": "2024-01-01", "end_date": "2024-01-31"},
    )

    assert resp.status_code == 200
    assert resp.get_json()["summary"] == {
        "securities": 4,
        "holdings": 6,
        "investment_transactions": 3,
        "items": 2,
    }


@pytest.fixture
def plaid_webhook_client():
    models_stub = types.ModuleType("app.models")
    models_stub.Account = type("Account", (), {})
    models_stub.PlaidAccount = PlaidAccountStub
    models_stub.PlaidWebhookLog = WebhookLogStub

    investments_logic_stub = types.ModuleType("app.sql.investments_logic")
    investments_logic_stub.upsert_investment_transactions = lambda txs: len(txs)
    investments_logic_stub.upsert_investments_from_plaid = lambda *_a, **_k: {
        "securities": 2,
        "holdings": 5,
    }

    account_logic_stub = types.ModuleType("app.sql.account_logic")
    account_logic_stub.refresh_data_for_plaid_account = lambda *_a, **_k: (True, None)

    sql_pkg = types.ModuleType("app.sql")
    sql_pkg.account_logic = account_logic_stub
    sql_pkg.investments_logic = investments_logic_stub
    sys.modules["app.sql.account_logic"] = account_logic_stub
    sys.modules["app.sql.investments_logic"] = investments_logic_stub

    helpers_stub = types.ModuleType("app.helpers.plaid_helpers")
    helpers_stub.get_accounts = lambda *_a, **_k: []
    helpers_stub.get_investment_transactions = lambda *_a, **_k: [
        {"id": "p1"},
        {"id": "p2"},
    ]

    module = _load_module(
        "app.routes.plaid_webhook",
        os.path.join(BASE_BACKEND, "app", "routes", "plaid_webhook.py"),
        models_stub,
        sql_pkg,
        helpers_stub=helpers_stub,
    )

    module._verify_plaid_signature = lambda _req: (True, None)

    app = Flask(__name__)
    app.register_blueprint(module.plaid_webhooks, url_prefix="/api/webhooks")
    with app.test_client() as client:
        yield client, module


def test_plaid_webhook_investments_transactions_dispatch(
    plaid_webhook_client, monkeypatch
):
    client, module = plaid_webhook_client

    acct = PlaidAccountStub("acct-1", "item-1", "token-1")
    module.PlaidAccount.query = PlaidQueryStub([acct])

    monkeypatch.setattr(
        module,
        "get_investment_transactions",
        lambda *_a, **_k: [{"id": "a"}, {"id": "b"}, {"id": "c"}],
    )
    monkeypatch.setattr(
        module.investments_logic, "upsert_investment_transactions", lambda txs: len(txs)
    )

    resp = client.post(
        "/api/webhooks/plaid",
        json={
            "webhook_type": "INVESTMENTS_TRANSACTIONS",
            "webhook_code": "DEFAULT_UPDATE",
            "item_id": "item-1",
        },
        headers={"Plaid-Signature": "t=1,v1=ok"},
    )

    assert resp.status_code == 200
    assert resp.get_json()["triggered"] == [
        {"account_id": "acct-1", "investment_txs": 3}
    ]


def test_plaid_webhook_holdings_dispatch(plaid_webhook_client, monkeypatch):
    client, module = plaid_webhook_client

    acct = PlaidAccountStub(
        "acct-9", "item-9", "token-9", account=types.SimpleNamespace(user_id="u9")
    )
    module.PlaidAccount.query = PlaidQueryStub([acct])
    monkeypatch.setattr(
        module.investments_logic,
        "upsert_investments_from_plaid",
        lambda _uid, _token: {"securities": 7, "holdings": 11},
    )

    resp = client.post(
        "/api/webhooks/plaid",
        json={
            "webhook_type": "HOLDINGS",
            "webhook_code": "DEFAULT_UPDATE",
            "item_id": "item-9",
        },
        headers={"Plaid-Signature": "t=1,v1=ok"},
    )

    assert resp.status_code == 200
    assert resp.get_json()["triggered"] == [
        {"account_id": "acct-9", "securities": 7, "holdings": 11}
    ]


def test_plaid_webhook_investments_missing_item_id_is_ignored(plaid_webhook_client):
    client, _module = plaid_webhook_client

    tx_resp = client.post(
        "/api/webhooks/plaid",
        json={
            "webhook_type": "INVESTMENTS_TRANSACTIONS",
            "webhook_code": "DEFAULT_UPDATE",
        },
        headers={"Plaid-Signature": "t=1,v1=ok"},
    )
    holdings_resp = client.post(
        "/api/webhooks/plaid",
        json={"webhook_type": "HOLDINGS", "webhook_code": "DEFAULT_UPDATE"},
        headers={"Plaid-Signature": "t=1,v1=ok"},
    )

    assert tx_resp.status_code == 200
    assert tx_resp.get_json()["status"] == "ignored"
    assert holdings_resp.status_code == 200
    assert holdings_resp.get_json()["status"] == "ignored"
