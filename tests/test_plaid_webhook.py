"""Tests for Plaid webhook processing and sync instrumentation."""

import hashlib
import hmac
import importlib.util
import json
import os
import sys
import types
from datetime import datetime, timezone
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

    def options(self, *args: object, **kwargs: object) -> "QueryStub":
        """Ignore eager-loading hints while retaining fluent API support."""

        return self

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

    def delete(self, synchronize_session: bool = False) -> int:  # noqa: ARG002 - parity with SQLAlchemy
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

    def __init__(self, account_id: str, user_id: str, balance: float = 0.0) -> None:
        self._account_id = account_id
        self.user_id = user_id
        self.balance = balance
        self.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)


class FakeAccountHistory:
    """Mutable representation of an ``AccountHistory`` row for assertions."""

    def __init__(self, balance: float = 0.0) -> None:
        self.balance = balance
        self.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)


class FakePlaidAccount:
    """Minimal Plaid account representation."""

    account: FakeAccount | None = None

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
    """Placeholder transaction capturing assigned attributes for assertions."""

    transaction_id = ColumnDescriptor("_transaction_id", "transaction_id")

    def __init__(self, transaction_id: str = "", **kwargs: object) -> None:
        self._transaction_id = transaction_id
        for key, value in kwargs.items():
            setattr(self, key, value)


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
config_stub.PLAID_WEBHOOK_SECRET = "test-secret"
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
    refresh_data_for_plaid_account=lambda *args, **kwargs: (True, None),
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
    def __init__(self, access_token: str, cursor: Optional[str] = None) -> None:
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
plaid_webhook_module.joinedload = lambda *args, **kwargs: None
sys.modules["app.routes.plaid_webhook"] = plaid_webhook_module

PLAID_SYNC_PATH = os.path.join(BASE_BACKEND, "app", "services", "plaid_sync.py")
plaid_sync_spec = importlib.util.spec_from_file_location(
    "tests.plaid_sync_under_test", PLAID_SYNC_PATH
)
plaid_sync_module = importlib.util.module_from_spec(plaid_sync_spec)
assert plaid_sync_spec.loader is not None
plaid_sync_spec.loader.exec_module(plaid_sync_module)

_restore_modules()


def _build_signature(
    payload: dict[str, object], timestamp: str = "1234567890"
) -> tuple[str, dict[str, str]]:
    """Return the serialized body and Plaid signature header for a payload."""

    body = json.dumps(payload)
    signature = hmac.new(
        config_stub.PLAID_WEBHOOK_SECRET.encode("utf-8"),
        msg=f"{timestamp}.{body}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    header = {"Plaid-Signature": f"t={timestamp},v1={signature}"}
    return body, header


@pytest.fixture(autouse=True)
def reset_metrics() -> None:
    """Reset webhook metrics between tests."""

    plaid_webhook_module.webhook_metrics.reset()


def test_webhook_accepts_valid_signature() -> None:
    """A valid signature should allow webhook processing to continue."""

    session = FakeSession()
    extensions_stub.db.session = session
    plaid_webhook_module.db.session = session
    plaid_webhook_module.PlaidWebhookLog = FakePlaidWebhookLog

    fake_logger = FakeLogger()
    config_stub.logger = fake_logger
    plaid_webhook_module.logger = fake_logger

    app = Flask(__name__)
    app.register_blueprint(plaid_webhook_module.plaid_webhooks)

    payload = {"webhook_type": "PING", "webhook_code": "TEST"}
    body, headers = _build_signature(payload)

    with app.test_client() as client:
        resp = client.post(
            "/plaid", data=body, headers=headers, content_type="application/json"
        )

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ignored"}
    assert session.commits == 1
    assert plaid_webhook_module.webhook_metrics.count("failure", "SIGNATURE") == 0
    assert not any(
        "Rejecting Plaid webhook" in msg for msg in fake_logger.records["warning"]
    )


def test_webhook_rejects_missing_signature() -> None:
    """Webhook calls without signatures are rejected with a 401."""

    session = FakeSession()
    extensions_stub.db.session = session
    plaid_webhook_module.db.session = session
    plaid_webhook_module.PlaidWebhookLog = FakePlaidWebhookLog

    fake_logger = FakeLogger()
    config_stub.logger = fake_logger
    plaid_webhook_module.logger = fake_logger

    app = Flask(__name__)
    app.register_blueprint(plaid_webhook_module.plaid_webhooks)

    payload = {"webhook_type": "PING", "webhook_code": "TEST"}
    body = json.dumps(payload)

    with app.test_client() as client:
        resp = client.post("/plaid", data=body, content_type="application/json")

    assert resp.status_code == 401
    assert resp.get_json() == {"status": "unauthorized"}
    assert session.commits == 0
    assert plaid_webhook_module.webhook_metrics.count("failure", "SIGNATURE") == 1
    assert any(
        "missing Plaid-Signature header" in msg
        for msg in fake_logger.records["warning"]
    )


def test_webhook_rejects_tampered_payload() -> None:
    """Webhook calls with mismatched signatures are rejected with a 403."""

    session = FakeSession()
    extensions_stub.db.session = session
    plaid_webhook_module.db.session = session
    plaid_webhook_module.PlaidWebhookLog = FakePlaidWebhookLog

    fake_logger = FakeLogger()
    config_stub.logger = fake_logger
    plaid_webhook_module.logger = fake_logger

    app = Flask(__name__)
    app.register_blueprint(plaid_webhook_module.plaid_webhooks)

    payload = {"webhook_type": "PING", "webhook_code": "TEST"}
    body, headers = _build_signature(payload)
    tampered_body = json.dumps({**payload, "item_id": "different"})

    with app.test_client() as client:
        resp = client.post(
            "/plaid",
            data=tampered_body,
            headers=headers,
            content_type="application/json",
        )

    assert resp.status_code == 403
    assert resp.get_json() == {"status": "unauthorized"}
    assert session.commits == 0
    assert plaid_webhook_module.webhook_metrics.count("failure", "SIGNATURE") == 1
    assert any(
        "invalid Plaid-Signature" in msg for msg in fake_logger.records["warning"]
    )


def test_sync_updates_available_triggers_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the webhook triggers syncs and records success metrics."""

    session = FakeSession()
    extensions_stub.db.session = session
    plaid_webhook_module.db.session = session

    fake_logger = FakeLogger()
    config_stub.logger = fake_logger
    plaid_webhook_module.logger = fake_logger

    account_a = FakeAccount("acct-1", "user-1", balance=100.0)
    account_b = FakeAccount("acct-2", "user-1", balance=200.0)
    plaid_a = FakePlaidAccount("acct-1", "item-1", "token-1")
    plaid_a.account = account_a
    plaid_b = FakePlaidAccount("acct-2", "item-1", "token-2")
    plaid_b.account = None  # Force route to resolve via Account.query

    plaid_accounts = [plaid_a, plaid_b]
    plaid_webhook_module.PlaidAccount.query = QueryStub(plaid_accounts)
    plaid_webhook_module.Account.query = QueryStub([account_a, account_b])

    calls: list[tuple[str, str]] = []
    lookup = {account_a.account_id: account_a, account_b.account_id: account_b}
    history_records = {
        account_a.account_id: FakeAccountHistory(balance=account_a.balance),
        account_b.account_id: FakeAccountHistory(balance=account_b.balance),
    }
    history_updates: dict[str, list[float]] = {}
    initial_history_stamps = {
        account_id: record.updated_at for account_id, record in history_records.items()
    }

    def fake_refresh(access_token: str, account_id: str) -> tuple[bool, None]:
        calls.append((access_token, account_id))
        acct = lookup[account_id]
        acct.balance += 10
        history_updates.setdefault(account_id, []).append(acct.balance)
        entry = history_records[account_id]
        entry.balance = acct.balance
        entry.updated_at = datetime.now(timezone.utc)
        return True, None

    monkeypatch.setattr(
        plaid_webhook_module.account_logic,
        "refresh_data_for_plaid_account",
        fake_refresh,
    )

    app = Flask(__name__)
    app.register_blueprint(plaid_webhook_module.plaid_webhooks)

    payload = {
        "webhook_type": "TRANSACTIONS",
        "webhook_code": "SYNC_UPDATES_AVAILABLE",
        "item_id": "item-1",
    }
    body, headers = _build_signature(payload)

    with app.test_client() as client:
        resp = client.post(
            "/plaid",
            data=body,
            headers=headers,
            content_type="application/json",
        )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"status": "ok", "triggered": ["acct-1", "acct-2"]}
    assert calls == [("token-1", "acct-1"), ("token-2", "acct-2")]
    assert history_updates == {"acct-1": [110.0], "acct-2": [210.0]}
    assert account_a.balance == 110.0
    assert account_b.balance == 210.0
    assert account_a.updated_at > datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert account_b.updated_at > datetime(2000, 1, 1, tzinfo=timezone.utc)
    assert plaid_a.last_refreshed is not None
    assert plaid_b.last_refreshed is not None
    for account_id, entry in history_records.items():
        assert entry.balance == lookup[account_id].balance
        assert entry.updated_at > initial_history_stamps[account_id]

    info_logs = fake_logger.records["info"]
    assert any(
        "Received Plaid webhook TRANSACTIONS:SYNC_UPDATES_AVAILABLE for item item-1"
        in msg
        for msg in info_logs
    )

    # One commit for the webhook log plus one per successful account refresh
    assert session.commits == 1 + len(plaid_accounts)
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


def test_sync_sets_provider_lowercase() -> None:
    """Ensure transactions synced from Plaid persist with a lowercase provider."""

    session = FakeSession()
    extensions_stub.db.session = session
    plaid_sync_module.db.session = session

    fake_logger = FakeLogger()
    config_stub.logger = fake_logger
    plaid_sync_module.logger = fake_logger

    account = FakeAccount("acct-1", "user-1")
    plaid_sync_module.Account.query = QueryStub([account])

    plaid_account = FakePlaidAccount("acct-1", "item-1", "tok-1")
    plaid_sync_module.PlaidAccount.query = QueryStub([plaid_account])

    existing_txn = FakeTransaction(
        transaction_id="txn-existing",
        amount=42.0,
        date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        description="Original purchase",
        pending=False,
        category_id=99,
        category="Legacy",
        merchant_name="Old Merchant",
        merchant_type="POS",
        provider="Plaid",
        personal_finance_category={"primary": "OLD"},
        personal_finance_category_icon_url="https://icon/old.png",
    )
    existing_txn.account_id = account.account_id

    plaid_sync_module.Transaction.query = QueryStub([existing_txn])

    added_tx = {
        "transaction_id": "txn-new",
        "account_id": account.account_id,
        "amount": 12.34,
        "date": "2024-02-01",
        "name": "Coffee Shop",
        "pending": False,
        "personal_finance_category": {"primary": "FOOD_AND_DRINK"},
        "personal_finance_category_icon_url": "https://icon/new.png",
    }

    modified_tx = {
        "transaction_id": existing_txn.transaction_id,
        "account_id": account.account_id,
        "amount": 100.0,
        "date": "2024-02-02",
        "name": "Updated Purchase",
        "pending": True,
        "personal_finance_category": {"primary": "GENERAL_MERCHANDISE"},
        "personal_finance_category_icon_url": "https://icon/update.png",
    }

    responses = [
        {
            "added": [added_tx],
            "modified": [modified_tx],
            "removed": [],
            "next_cursor": "CUR-LOWER",
            "has_more": False,
        }
    ]
    plaid_sync_module.plaid_client = FakePlaidClient(responses)

    result = plaid_sync_module.sync_account_transactions(account.account_id)

    assert result["added"] == 1
    assert result["modified"] == 1

    assert session.added, "Expected new transaction to be persisted"
    new_txn = next(
        (
            obj
            for obj in session.added
            if getattr(obj, "transaction_id", "") == "txn-new"
        ),
        None,
    )
    assert new_txn is not None
    assert getattr(new_txn, "provider", None) == "plaid"
    assert existing_txn.provider == "plaid"
