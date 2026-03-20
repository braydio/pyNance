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

    def join(self, *_args, **_kwargs):
        return self


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

    def options(self, *_args, **_kwargs):
        return self

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


class AccountScopeStub:
    """Minimal account model for user and investment scope assertions."""

    account_id = FilterColumn("account_id")

    def __init__(self, account_id: str, user_id: str, is_investment: bool):
        self.account_id = account_id
        self.user_id = user_id
        self.is_investment = is_investment


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
    models_stub.Account = AccountScopeStub
    models_stub.PlaidAccount = PlaidAccountStub
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

    scoped_account_rows = [
        {
            "account_id": "acc-1",
            "user_id": "u1",
            "name": "Brokerage 1",
            "institution_name": "Inst 1",
        }
    ]
    captured_scope = {"user_id": None}

    investments_logic_stub = types.ModuleType("app.sql.investments_logic")

    def _get_accounts(user_id=None):
        captured_scope["user_id"] = user_id
        return [row for row in scoped_account_rows if row["user_id"] == user_id]

    investments_logic_stub.get_investment_accounts = _get_accounts

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
    cross_user_holding = Holding("acc-2", "sec-2", 3.0, 11.0, 33.0, date(2024, 5, 2))
    non_investment_holding = Holding(
        "acc-3", "sec-3", 4.0, 12.0, 48.0, date(2024, 5, 2)
    )
    no_scope_holding = Holding("acc-4", "sec-4", 5.0, 13.0, 65.0, date(2024, 5, 2))
    security = Sec(
        "sec-1", "Security One", "SEC1", "equity", "USD", 15.0, date(2024, 5, 2)
    )
    security_two = Sec(
        "sec-2", "Security Two", "SEC2", "equity", "USD", 16.0, date(2024, 5, 2)
    )
    security_three = Sec(
        "sec-3", "Security Three", "SEC3", "equity", "USD", 17.0, date(2024, 5, 2)
    )
    security_four = Sec(
        "sec-4", "Security Four", "SEC4", "equity", "USD", 18.0, date(2024, 5, 2)
    )

    allowed_account = AccountScopeStub("acc-1", "u1", True)
    cross_user_account = AccountScopeStub("acc-2", "u2", True)
    non_investment_account = AccountScopeStub("acc-3", "u1", False)
    no_scope_account = AccountScopeStub("acc-4", "u1", True)

    plaid_investments = PlaidAccountStub(
        "acc-1", "item-1", "token-1", product="investments"
    )
    plaid_investments_two = PlaidAccountStub(
        "acc-2", "item-2", "token-2", product="investments"
    )
    plaid_non_investments = PlaidAccountStub(
        "acc-3", "item-3", "token-3", product="transactions"
    )
    plaid_missing_scope = PlaidAccountStub(
        "acc-4", "item-4", "token-4", product="liabilities"
    )

    class SessionQuery:
        def __init__(self):
            self.rows = [
                (holding, security, allowed_account, plaid_investments),
                (
                    cross_user_holding,
                    security_two,
                    cross_user_account,
                    plaid_investments_two,
                ),
                (
                    non_investment_holding,
                    security_three,
                    non_investment_account,
                    plaid_non_investments,
                ),
                (
                    no_scope_holding,
                    security_four,
                    no_scope_account,
                    plaid_missing_scope,
                ),
            ]

        def join(self, *_args, **_kwargs):
            return self

        def all(self):
            return list(self.rows)

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
        Txn(
            "t4",
            "acc-3",
            "sec-3",
            date(2024, 1, 4),
            40.0,
            4.0,
            10.0,
            "buy",
            "trade",
            "fourth",
            0.0,
            "USD",
        ),
        Txn(
            "t5",
            "acc-4",
            "sec-4",
            date(2024, 1, 5),
            50.0,
            5.0,
            10.0,
            "buy",
            "trade",
            "fifth",
            0.0,
            "USD",
        ),
    ]

    class JoinedTxnQuery(QueryListStub):
        def all(self):
            account_by_id = {
                "acc-1": allowed_account,
                "acc-2": cross_user_account,
                "acc-3": non_investment_account,
                "acc-4": no_scope_account,
            }
            plaid_by_id = {
                "acc-1": plaid_investments,
                "acc-2": plaid_investments_two,
                "acc-3": plaid_non_investments,
                "acc-4": plaid_missing_scope,
            }
            return [
                (txn, account_by_id[txn.account_id], plaid_by_id[txn.account_id])
                for txn in self._rows
            ]

    models_stub.InvestmentTransaction.query = JoinedTxnQuery(txns)

    app = Flask(__name__)
    app.register_blueprint(module.investments, url_prefix="/api/investments")
    with app.test_client() as client:
        yield client, module, models_stub, txns, captured_scope


def test_investments_success_endpoints(investments_client):
    client, _module, _models_stub, _txns, captured_scope = investments_client

    accounts_resp = client.get("/api/investments/accounts?user_id=u1")
    holdings_resp = client.get("/api/investments/holdings?user_id=u1")
    tx_resp = client.get("/api/investments/transactions?user_id=u1")

    assert accounts_resp.status_code == 200
    assert holdings_resp.status_code == 200
    assert tx_resp.status_code == 200
    assert captured_scope["user_id"] == "u1"
    assert accounts_resp.get_json()["data"][0]["account_id"] == "acc-1"
    assert holdings_resp.get_json()["data"][0]["security"]["ticker_symbol"] == "SEC1"
    assert tx_resp.get_json()["data"]["total"] == 2


def test_investments_transactions_date_validation_errors(investments_client):
    client, *_ = investments_client

    bad_format = client.get(
        "/api/investments/transactions?user_id=u1&start_date=2024/01/01"
    )
    reversed_range = client.get(
        "/api/investments/transactions?user_id=u1&start_date=2024-02-02&end_date=2024-01-01"
    )

    assert bad_format.status_code == 400
    assert "Invalid date" in bad_format.get_json()["error"]
    assert reversed_range.status_code == 400
    assert (
        "end_date must be greater than or equal" in reversed_range.get_json()["error"]
    )


def test_investments_transactions_combined_filters_and_pagination(investments_client):
    client, _module, models_stub, txns, _captured_scope = investments_client
    models_stub.InvestmentTransaction.query = (
        models_stub.InvestmentTransaction.query.__class__(txns)
    )

    resp = client.get(
        "/api/investments/transactions?user_id=u1&account_id=acc-1&security_id=sec-1&type=trade&subtype=buy"
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


def test_investments_endpoints_require_user_scope(investments_client):
    client, *_ = investments_client

    accounts_resp = client.get("/api/investments/accounts")
    holdings_resp = client.get("/api/investments/holdings")
    tx_resp = client.get("/api/investments/transactions")

    assert accounts_resp.status_code == 400
    assert holdings_resp.status_code == 400
    assert tx_resp.status_code == 400


def test_investments_filters_cross_user_and_non_investment_results(investments_client):
    client, *_ = investments_client

    holdings_resp = client.get("/api/investments/holdings?user_id=u1")
    tx_resp = client.get("/api/investments/transactions?user_id=u1")

    holding_accounts = [row["account_id"] for row in holdings_resp.get_json()["data"]]
    tx_accounts = [
        row["account_id"] for row in tx_resp.get_json()["data"]["transactions"]
    ]

    assert holding_accounts == ["acc-1"]
    assert tx_accounts == ["acc-1", "acc-1"]


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
    account_logic_stub.canonicalize_plaid_products = lambda value: [
        token.strip() for token in str(value or "").split(",") if token.strip()
    ]
    account_logic_stub.merge_plaid_products = lambda existing, incoming: ",".join(
        sorted(
            {
                token.strip()
                for raw in (existing, incoming)
                for token in str(raw or "").split(",")
                if token.strip()
            }
        )
    )
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


@pytest.mark.parametrize(
    ("path", "expected_error"),
    [
        ("/api/plaid/investments/generate_link_token", "Missing user_id"),
        (
            "/api/plaid/investments/exchange_public_token",
            "Missing user_id or public_token",
        ),
        ("/api/plaid/investments/refresh", "Missing user_id or item_id"),
    ],
)
def test_plaid_investments_rejects_empty_body(
    plaid_investments_client, path, expected_error
):
    """Return deterministic 400 responses when required JSON fields are absent."""
    client, _module = plaid_investments_client

    response = client.post(path)

    assert response.status_code == 400
    assert response.get_json() == {"error": expected_error}


@pytest.mark.parametrize(
    ("path", "expected_error"),
    [
        ("/api/plaid/investments/generate_link_token", "Missing user_id"),
        (
            "/api/plaid/investments/exchange_public_token",
            "Missing user_id or public_token",
        ),
        ("/api/plaid/investments/refresh", "Missing user_id or item_id"),
    ],
)
def test_plaid_investments_rejects_invalid_json_body(
    plaid_investments_client, path, expected_error
):
    """Treat malformed JSON payloads as empty input and return 400 validation errors."""
    client, _module = plaid_investments_client

    response = client.post(path, data="{", content_type="application/json")

    assert response.status_code == 400
    assert response.get_json() == {"error": expected_error}


@pytest.mark.parametrize(
    ("path", "expected_error"),
    [
        ("/api/plaid/investments/generate_link_token", "Missing user_id"),
        (
            "/api/plaid/investments/exchange_public_token",
            "Missing user_id or public_token",
        ),
        ("/api/plaid/investments/refresh", "Missing user_id or item_id"),
    ],
)
def test_plaid_investments_rejects_non_object_json_body(
    plaid_investments_client, path, expected_error
):
    """Treat non-object JSON payloads as empty input for deterministic validation."""
    client, _module = plaid_investments_client

    response = client.post(path, json=["not", "an", "object"])

    assert response.status_code == 400
    assert response.get_json() == {"error": expected_error}


def test_plaid_investments_generate_link_token_success(plaid_investments_client):
    """Return a Plaid link token for valid investment link requests."""
    client, _module = plaid_investments_client

    response = client.post(
        "/api/plaid/investments/generate_link_token", json={"user_id": "u1"}
    )

    assert response.status_code == 200
    assert response.get_json() == {"status": "success", "link_token": "link-token"}


def test_plaid_investments_exchange_public_token_success(plaid_investments_client):
    """Exchange public token requests return the linked item id on success."""
    client, _module = plaid_investments_client

    response = client.post(
        "/api/plaid/investments/exchange_public_token",
        json={"user_id": "u1", "public_token": "public-token"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"status": "success", "item_id": "item"}


def test_plaid_investments_exchange_public_token_merges_existing_item_scopes(
    plaid_investments_client, monkeypatch
):
    """Linking investments later preserves existing transactions product scope."""
    client, module = plaid_investments_client

    existing_item = types.SimpleNamespace(
        access_token="old-token",
        user_id="old-user",
        product="transactions",
        is_active=False,
    )
    module.PlaidItem.query = types.SimpleNamespace(
        filter_by=lambda **_k: types.SimpleNamespace(first=lambda: existing_item)
    )

    saved_products = []
    upsert_enabled_products = []
    monkeypatch.setattr(
        module,
        "save_plaid_account",
        lambda _acct_id, _item_id, _access_token, product: saved_products.append(
            product
        ),
    )
    monkeypatch.setattr(
        module,
        "upsert_accounts",
        lambda *_a, **kwargs: upsert_enabled_products.append(
            kwargs.get("enabled_products")
        ),
    )
    monkeypatch.setattr(
        module,
        "get_accounts",
        lambda *_a, **_k: [{"account_id": "acc-1"}, {"account_id": "acc-2"}],
    )

    response = client.post(
        "/api/plaid/investments/exchange_public_token",
        json={"user_id": "u1", "public_token": "public-token"},
    )

    assert response.status_code == 200
    assert existing_item.product == "investments,transactions"
    assert upsert_enabled_products == ["investments,transactions"]
    assert saved_products == ["investments,transactions", "investments,transactions"]


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


def test_plaid_investments_refresh_supports_canonical_scope_strings(
    plaid_investments_client, monkeypatch
):
    """Refresh should match accounts whose product scopes include investments."""
    client, module = plaid_investments_client

    account = PlaidAccountStub(
        "acct-1", "item-1", "token-1", product="investments,transactions"
    )
    module.PlaidAccount.query = PlaidQueryStub([account])

    monkeypatch.setattr(
        module.investments_logic,
        "upsert_investments_from_plaid",
        lambda _user_id, _token: {"securities": 1, "holdings": 1},
    )
    monkeypatch.setattr(
        module, "get_investment_transactions", lambda *_a: [{"id": "a"}]
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
    assert resp.get_json()["upserts"]["investment_transactions"] == 1


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
    account_logic_stub.canonicalize_plaid_products = lambda value: [
        token.strip() for token in str(value or "").split(",") if token.strip()
    ]

    sql_pkg = types.ModuleType("app.sql")
    sql_pkg.account_logic = account_logic_stub
    sql_pkg.investments_logic = investments_logic_stub
    sys.modules["app.sql.account_logic"] = account_logic_stub
    sys.modules["app.sql.investments_logic"] = investments_logic_stub

    plaid_sync_stub = types.ModuleType("app.services.plaid_sync")
    plaid_sync_stub.sync_account_transactions = lambda _account_id: {"ok": True}
    services_pkg = types.ModuleType("app.services")
    services_pkg.plaid_sync = plaid_sync_stub
    sys.modules["app.services"] = services_pkg
    sys.modules["app.services.plaid_sync"] = plaid_sync_stub

    helpers_stub = types.ModuleType("app.helpers.plaid_helpers")
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


def test_plaid_webhook_transactions_sync_dispatches_each_account(
    plaid_webhook_client, monkeypatch
):
    client, module = plaid_webhook_client

    first = PlaidAccountStub(
        "acct-1", "item-1", "token-1", account=types.SimpleNamespace()
    )
    second = PlaidAccountStub(
        "acct-2", "item-1", "token-1", account=types.SimpleNamespace()
    )
    module.PlaidAccount.query = PlaidQueryStub([first, second])
    module.PlaidAccount.account = None
    module.joinedload = lambda *_a, **_k: None

    called = []

    def _sync(account_id):
        called.append(account_id)
        return {"added": 1}

    monkeypatch.setattr(module.plaid_sync, "sync_account_transactions", _sync)

    resp = client.post(
        "/api/webhooks/plaid",
        json={
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "SYNC_UPDATES_AVAILABLE",
            "item_id": "item-1",
        },
        headers={"Plaid-Signature": "t=1,v1=ok"},
    )

    assert resp.status_code == 200
    assert called == ["acct-1", "acct-2"]
    assert resp.get_json()["triggered"] == ["acct-1", "acct-2"]


def test_plaid_webhook_transactions_sync_isolates_account_failures(
    plaid_webhook_client, monkeypatch
):
    client, module = plaid_webhook_client

    first = PlaidAccountStub(
        "acct-1", "item-1", "token-1", account=types.SimpleNamespace()
    )
    second = PlaidAccountStub(
        "acct-2", "item-1", "token-1", account=types.SimpleNamespace()
    )
    module.PlaidAccount.query = PlaidQueryStub([first, second])
    module.PlaidAccount.account = None
    module.joinedload = lambda *_a, **_k: None

    def _sync(account_id):
        if account_id == "acct-1":
            raise RuntimeError("boom")
        return {"added": 1}

    monkeypatch.setattr(module.plaid_sync, "sync_account_transactions", _sync)

    resp = client.post(
        "/api/webhooks/plaid",
        json={
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "DEFAULT_UPDATE",
            "item_id": "item-1",
        },
        headers={"Plaid-Signature": "t=1,v1=ok"},
    )

    assert resp.status_code == 200
    assert resp.get_json()["triggered"] == ["acct-2"]


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


def test_plaid_webhook_investments_transactions_accepts_mixed_product_scopes(
    plaid_webhook_client, monkeypatch
):
    """Webhook dispatch should include accounts with canonical mixed Plaid scopes."""
    client, module = plaid_webhook_client

    acct = PlaidAccountStub(
        "acct-1", "item-1", "token-1", product="investments,transactions"
    )
    module.PlaidAccount.query = PlaidQueryStub([acct])

    monkeypatch.setattr(
        module, "get_investment_transactions", lambda *_a, **_k: [{"id": "a"}]
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
        {"account_id": "acct-1", "investment_txs": 1}
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
