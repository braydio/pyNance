"""Tests for Plaid webhook processing and sync instrumentation."""

import importlib.util
import os
import sys
import types
from datetime import datetime
from typing import Iterable, List, Optional

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

_ORIGINAL_MODULES: dict[str, Optional[types.ModuleType]] = {}


def _set_module(name: str, module: types.ModuleType) -> None:
    """Record the original module (if any) and register a stub."""

    if name not in _ORIGINAL_MODULES:
        _ORIGINAL_MODULES[name] = sys.modules.get(name)
    sys.modules[name] = module


def _restore_modules() -> None:
    """Restore previously registered modules after stub-based imports."""

    for name, original in _ORIGINAL_MODULES.items():
        if original is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original


class FakeLogger:
    """Capture log calls while mimicking the logging API."""

    def __init__(self) -> None:
        self.records: dict[str, list[str]] = {
            "info": [],
            "warning": [],
            "error": [],
            "debug": [],
        }

    def _record(self, level: str, message: str, *args: object) -> None:
        if args:
            try:
                formatted = message % args
            except TypeError:
                formatted = message
        else:
            formatted = message
        self.records[level].append(formatted)

    def info(self, message: str, *args: object, **kwargs: object) -> None:
        self._record("info", message, *args)

    def warning(self, message: str, *args: object, **kwargs: object) -> None:
        self._record("warning", message, *args)

    def error(self, message: str, *args: object, **kwargs: object) -> None:
        self._record("error", message, *args)

    def debug(self, message: str, *args: object, **kwargs: object) -> None:
        self._record("debug", message, *args)


class FakeSession:
    """Lightweight stand-in for a SQLAlchemy session."""

    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0
        self.rollbacks = 0

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class ColumnDescriptor:
    """Descriptor that mimics ``Column.in_`` for query stubs."""

    def __init__(self, attr_name: str, lookup_name: Optional[str] = None) -> None:
        self.attr_name = attr_name
        self.lookup_name = lookup_name or attr_name.lstrip("_")

    def __get__(self, instance: object, owner: type) -> object:
        if instance is None:
            return self
        return getattr(instance, self.attr_name)

    def __set__(self, instance: object, value: object) -> None:
        setattr(instance, self.attr_name, value)

    def in_(self, values: Iterable[str]) -> tuple[str, List[str]]:
        return (f"{self.lookup_name}_in", list(values))


class QueryStub:
    """Simplified query helper supporting ``filter``/``filter_by``/``delete``."""

    def __init__(
        self, items: Iterable[object], deleted_log: Optional[List[str]] = None
    ) -> None:
        self._items = list(items)
        self._deleted_log = deleted_log
        self._pending_delete_ids: Optional[List[str]] = None

    def filter_by(self, **kwargs: object) -> "QueryStub":
        filtered = [
            obj
            for obj in self._items
            if all(getattr(obj, key, None) == value for key, value in kwargs.items())
        ]
        return QueryStub(filtered, self._deleted_log)

    def filter(self, condition: object) -> "QueryStub":
        if isinstance(condition, tuple):
            key, values = condition
            if key == "account_id_in":
                filtered = [
                    obj
                    for obj in self._items
                    if getattr(obj, "account_id", None) in values
                ]
                return QueryStub(filtered, self._deleted_log)
            if key == "transaction_id_in":
                self._pending_delete_ids = list(values)
                return self
        return self

    def all(self) -> List[object]:
        return list(self._items)

    def first(self) -> Optional[object]:
        return self._items[0] if self._items else None

    def delete(
        self, synchronize_session: bool = False
    ) -> int:  # noqa: ARG002 - parity with SQLAlchemy
        if not self._pending_delete_ids:
            return 0
        if self._deleted_log is not None:
            self._deleted_log.extend(self._pending_delete_ids)
        count = len(self._pending_delete_ids)
        self._pending_delete_ids = None
        return count


class FakePlaidWebhookLog:
    """Minimal Plaid webhook log model storing provided kwargs."""

    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


class FakeCategory:
    """Simplified transaction category."""

    def __init__(self, category_id: int = 1, display_name: str = "Category") -> None:
        self.id = category_id
        self.display_name = display_name


class FakeAccount:
    """Minimal account model for sync tests."""

    account_id = ColumnDescriptor("_account_id", "account_id")

    def __init__(self, account_id: str, user_id: str) -> None:
        self._account_id = account_id
        self.user_id = user_id


class FakePlaidAccount:
    """Minimal Plaid account representation."""

    def __init__(
        self,
        account_id: str,
        item_id: str,
        access_token: str,
        product: str = "transactions",
        sync_cursor: Optional[str] = None,
    ) -> None:
        self.account_id = account_id
        self.item_id = item_id
        self.access_token = access_token
        self.product = product
        self.sync_cursor = sync_cursor
        self.last_refreshed: Optional[datetime] = None
        self.account: Optional[FakeAccount] = None


class FakeTransaction:
    """Placeholder transaction used for removal tests."""

    transaction_id = ColumnDescriptor("_transaction_id", "transaction_id")

    def __init__(self, transaction_id: str = "") -> None:
        self._transaction_id = transaction_id


class FakePlaidItem:
    """Minimal Plaid item placeholder."""

    def __init__(self, item_id: str = "") -> None:
        self.item_id = item_id


class FakePlaidResponse:
    """Wrap a dict and expose ``to_dict`` like the Plaid SDK."""

    def __init__(self, data: dict[str, object]) -> None:
        self._data = data

    def to_dict(self) -> dict[str, object]:
        return dict(self._data)


class FakePlaidClient:
    """Stub Plaid client returning canned sync responses."""

    def __init__(self, responses: Iterable[dict[str, object]]) -> None:
        self._responses = list(responses)
        self.calls: list[object] = []

    def transactions_sync(self, request: object) -> FakePlaidResponse:
        self.calls.append(request)
        data = self._responses.pop(0)
        return FakePlaidResponse(data)


# --- Module stubs -------------------------------------------------------

config_stub = types.ModuleType("app.config")
config_stub.logger = FakeLogger()
config_stub.plaid_client = None
_set_module("app.config", config_stub)

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(session=FakeSession())
_set_module("app.extensions", extensions_stub)

helpers_pkg = types.ModuleType("app.helpers")
plaid_helpers_stub = types.ModuleType("app.helpers.plaid_helpers")
plaid_helpers_stub.get_investment_transactions = lambda *args, **kwargs: []
helpers_pkg.plaid_helpers = plaid_helpers_stub
_set_module("app.helpers", helpers_pkg)
_set_module("app.helpers.plaid_helpers", plaid_helpers_stub)

sql_pkg = types.ModuleType("app.sql")
investments_logic_stub = types.SimpleNamespace(
    upsert_investment_transactions=lambda txs: len(txs),
    upsert_investments_from_plaid=lambda *args, **kwargs: {},
)
transaction_rules_logic_stub = types.SimpleNamespace(
    apply_rules=lambda user_id, tx: tx,
)
refresh_metadata_stub = types.SimpleNamespace(
    refresh_or_insert_plaid_metadata=lambda *args, **kwargs: None,
)
account_logic_stub = types.SimpleNamespace(
    detect_internal_transfer=lambda *args, **kwargs: None,
    get_or_create_category=lambda *args, **kwargs: FakeCategory(),
    normalize_balance=lambda balance: balance,
)
sql_pkg.investments_logic = investments_logic_stub
sql_pkg.transaction_rules_logic = transaction_rules_logic_stub
sql_pkg.refresh_metadata = refresh_metadata_stub
sql_pkg.account_logic = account_logic_stub
_set_module("app.sql", sql_pkg)
_set_module("app.sql", sql_pkg)
_set_module("app.sql.investments_logic", investments_logic_stub)
_set_module("app.sql.transaction_rules_logic", transaction_rules_logic_stub)
_set_module("app.sql.refresh_metadata", refresh_metadata_stub)
_set_module("app.sql.account_logic", account_logic_stub)

models_stub = types.ModuleType("app.models")
models_stub.PlaidAccount = FakePlaidAccount
models_stub.PlaidWebhookLog = FakePlaidWebhookLog
models_stub.Account = FakeAccount
models_stub.Transaction = FakeTransaction
models_stub.Category = FakeCategory
models_stub.PlaidItem = FakePlaidItem
_set_module("app.models", models_stub)

services_pkg = types.ModuleType("app.services")
plaid_sync_stub = types.ModuleType("app.services.plaid_sync")


def _placeholder_sync(account_id: str) -> None:  # pragma: no cover - replaced in tests
    raise AssertionError("sync_account_transactions should be patched in tests")


plaid_sync_stub.sync_account_transactions = _placeholder_sync
services_pkg.plaid_sync = plaid_sync_stub
_set_module("app.services", services_pkg)
_set_module("app.services.plaid_sync", plaid_sync_stub)

plaid_pkg = types.ModuleType("plaid")
plaid_model_pkg = types.ModuleType("plaid.model")
transactions_sync_stub = types.ModuleType("plaid.model.transactions_sync_request")


class DummyTransactionsSyncRequest:
    def __init__(self, access_token: str, cursor: Optional[str]) -> None:
        self.access_token = access_token
        self.cursor = cursor


def _install_plaid_package() -> None:
    transactions_sync_stub.TransactionsSyncRequest = DummyTransactionsSyncRequest
    plaid_pkg.model = plaid_model_pkg
    plaid_model_pkg.transactions_sync_request = transactions_sync_stub
    _set_module("plaid", plaid_pkg)
    _set_module("plaid.model", plaid_model_pkg)
    _set_module("plaid.model.transactions_sync_request", transactions_sync_stub)


_install_plaid_package()

PLAID_WEBHOOK_PATH = os.path.join(BASE_BACKEND, "app", "routes", "plaid_webhook.py")
plaid_webhook_spec = importlib.util.spec_from_file_location(
    "app.routes.plaid_webhook", PLAID_WEBHOOK_PATH
)
plaid_webhook_module = importlib.util.module_from_spec(plaid_webhook_spec)
assert plaid_webhook_spec.loader is not None
plaid_webhook_spec.loader.exec_module(plaid_webhook_module)
sys.modules["app.routes.plaid_webhook"] = plaid_webhook_module

PLAID_SYNC_PATH = os.path.join(BASE_BACKEND, "app", "services", "plaid_sync.py")
plaid_sync_spec = importlib.util.spec_from_file_location(
    "tests.plaid_sync_under_test", PLAID_SYNC_PATH
)
plaid_sync_module = importlib.util.module_from_spec(plaid_sync_spec)
assert plaid_sync_spec.loader is not None
plaid_sync_spec.loader.exec_module(plaid_sync_module)

_restore_modules()


@pytest.fixture(autouse=True)
def reset_metrics() -> None:
    """Reset webhook metrics between tests."""

    plaid_webhook_module.webhook_metrics.reset()


def test_sync_updates_available_triggers_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the webhook triggers syncs and records success metrics."""

    session = FakeSession()
    extensions_stub.db.session = session
    plaid_webhook_module.db.session = session

    fake_logger = FakeLogger()
    config_stub.logger = fake_logger
    plaid_webhook_module.logger = fake_logger

    accounts = [
        FakePlaidAccount("acct-1", "item-1", "token-1"),
        FakePlaidAccount("acct-2", "item-1", "token-2"),
    ]
    plaid_webhook_module.PlaidAccount.query = QueryStub(accounts)

    calls: list[str] = []

    def fake_sync(account_id: str) -> dict[str, str]:
        calls.append(account_id)
        return {"account_id": account_id}

    monkeypatch.setattr(plaid_webhook_module, "sync_account_transactions", fake_sync)

    app = Flask(__name__)
    app.register_blueprint(plaid_webhook_module.plaid_webhooks)

    with app.test_client() as client:
        resp = client.post(
            "/plaid",
            json={
                "webhook_type": "TRANSACTIONS",
                "webhook_code": "SYNC_UPDATES_AVAILABLE",
                "item_id": "item-1",
            },
        )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"status": "ok", "triggered": ["acct-1", "acct-2"]}
    assert calls == ["acct-1", "acct-2"]

    assert session.commits == 1
    assert len(session.added) == 1
    log_entry = session.added[0]
    assert log_entry.event_type == "TRANSACTIONS:SYNC_UPDATES_AVAILABLE"

    assert (
        plaid_webhook_module.webhook_metrics.count("success", "SYNC_UPDATES_AVAILABLE")
        == 2
    )
    assert (
        plaid_webhook_module.webhook_metrics.count("failure", "SYNC_UPDATES_AVAILABLE")
        == 0
    )


def test_sync_persists_cursor_and_handles_removed_transactions() -> None:
    """Validate cursor updates and removed transaction processing."""

    session = FakeSession()
    extensions_stub.db.session = session

    fake_logger = FakeLogger()
    config_stub.logger = fake_logger
    plaid_sync_module.logger = fake_logger

    deleted_ids: list[str] = []
    plaid_sync_module.Transaction.query = QueryStub([], deleted_ids)

    account_main = FakeAccount("acct-1", "user-1")
    account_secondary = FakeAccount("acct-2", "user-1")
    plaid_sync_module.Account.query = QueryStub([account_main, account_secondary])

    plaid_account_main = FakePlaidAccount("acct-1", "item-1", "tok-1")
    plaid_account_secondary = FakePlaidAccount(
        "acct-2", "item-1", "tok-1", sync_cursor="CUR-EXIST"
    )
    plaid_sync_module.PlaidAccount.query = QueryStub(
        [plaid_account_main, plaid_account_secondary]
    )

    responses = [
        {
            "added": [],
            "modified": [],
            "removed": [{"transaction_id": "tx-removed"}],
            "next_cursor": "CUR-NEXT",
            "has_more": False,
        }
    ]
    fake_client = FakePlaidClient(responses)
    plaid_sync_module.plaid_client = fake_client

    result = plaid_sync_module.sync_account_transactions("acct-1")

    assert result["next_cursor"] == "CUR-NEXT"
    assert result["removed"] == 1
    assert session.commits == 3
    assert session.rollbacks == 0
    assert deleted_ids == ["tx-removed"]
    assert plaid_account_main.sync_cursor == "CUR-NEXT"
    assert plaid_account_secondary.sync_cursor == "CUR-NEXT"
    assert plaid_account_main.last_refreshed is not None
    assert plaid_account_secondary.last_refreshed is not None
    assert fake_client.calls and fake_client.calls[0].cursor == "CUR-EXIST"
