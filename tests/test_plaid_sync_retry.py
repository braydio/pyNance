"""Unit tests for Plaid sync retry handling."""

import importlib.util
import os
import sys
import types


class _DummyLogger:
    def __init__(self):
        self.events = []

    def warning(self, message, extra=None):
        self.events.append(("warning", message, extra or {}))

    def error(self, message, extra=None):
        self.events.append(("error", message, extra or {}))


class _PlaidError(Exception):
    def __init__(self, error_code, body=None):
        super().__init__(error_code)
        self.error_code = error_code
        self.body = body


def _load_plaid_sync_module():
    """Load plaid_sync with minimal app module stubs for isolated tests."""

    app_stub = types.ModuleType("app")
    config_stub = types.ModuleType("app.config")
    extensions_stub = types.ModuleType("app.extensions")
    models_stub = types.ModuleType("app.models")
    sql_pkg_stub = types.ModuleType("app.sql")
    rules_stub = types.ModuleType("app.sql.transaction_rules_logic")
    account_logic_stub = types.ModuleType("app.sql.account_logic")
    refresh_stub = types.ModuleType("app.sql.refresh_metadata")
    seq_stub = types.ModuleType("app.sql.sequence_utils")
    merchant_stub = types.ModuleType("app.utils.merchant_normalization")

    logger = _DummyLogger()
    config_stub.logger = logger
    config_stub.plaid_client = types.SimpleNamespace(transactions_sync=lambda _req: None)

    extensions_stub.db = types.SimpleNamespace(session=types.SimpleNamespace())
    models_stub.Account = object
    models_stub.Category = object
    models_stub.PlaidAccount = object
    models_stub.Transaction = object

    rules_stub.apply_rules = lambda _user_id, tx: tx
    account_logic_stub.detect_internal_transfer = lambda _tx: None
    account_logic_stub.get_or_create_category = lambda *_a, **_k: types.SimpleNamespace(
        id="cat-1",
        computed_display_name="Unknown",
        category_slug="unknown",
    )
    refresh_stub.refresh_or_insert_plaid_metadata = lambda *_a, **_k: None
    seq_stub.ensure_transactions_sequence = lambda: None
    merchant_stub.resolve_merchant = lambda **_kwargs: types.SimpleNamespace(
        display_name="Unknown",
        merchant_slug="unknown",
    )

    sys.modules["app"] = app_stub
    sys.modules["app.config"] = config_stub
    sys.modules["app.extensions"] = extensions_stub
    sys.modules["app.models"] = models_stub
    sys.modules["app.sql"] = sql_pkg_stub
    sys.modules["app.sql.transaction_rules_logic"] = rules_stub
    sys.modules["app.sql.account_logic"] = account_logic_stub
    sys.modules["app.sql.refresh_metadata"] = refresh_stub
    sys.modules["app.sql.sequence_utils"] = seq_stub
    sys.modules["app.utils.merchant_normalization"] = merchant_stub

    module_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "backend",
        "app",
        "services",
        "plaid_sync.py",
    )
    spec = importlib.util.spec_from_file_location("plaid_sync_retry_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module, logger


def test_transactions_sync_with_retry_retries_transient_errors(monkeypatch):
    module, logger = _load_plaid_sync_module()

    calls = {"count": 0}

    def _transactions_sync(_req):
        calls["count"] += 1
        if calls["count"] < 3:
            raise _PlaidError("RATE_LIMIT_EXCEEDED")
        return {"ok": True}

    monkeypatch.setattr(module.plaid_client, "transactions_sync", _transactions_sync)
    monkeypatch.setattr(module.time, "sleep", lambda *_a, **_k: None)

    response = module._transactions_sync_with_retry(
        req=object(),
        account_id="acc-1",
        item_id="item-1",
        max_attempts=3,
        initial_backoff_seconds=0,
    )

    assert response == {"ok": True}
    assert calls["count"] == 3
    warning_events = [event for event in logger.events if event[0] == "warning"]
    assert len(warning_events) == 2
    assert all(event[2]["error_code"] == "RATE_LIMIT_EXCEEDED" for event in warning_events)
    assert all(event[2]["account_id"] == "acc-1" for event in warning_events)
    assert all(event[2]["item_id"] == "item-1" for event in warning_events)
    assert warning_events[-1][2]["attempt_count"] == 2


def test_transactions_sync_with_retry_raises_non_transient(monkeypatch):
    module, logger = _load_plaid_sync_module()

    def _transactions_sync(_req):
        raise _PlaidError("INVALID_ACCESS_TOKEN")

    monkeypatch.setattr(module.plaid_client, "transactions_sync", _transactions_sync)

    try:
        module._transactions_sync_with_retry(
            req=object(),
            account_id="acc-2",
            item_id="item-2",
            max_attempts=3,
            initial_backoff_seconds=0,
        )
    except _PlaidError as exc:
        assert exc.error_code == "INVALID_ACCESS_TOKEN"
    else:
        raise AssertionError("Expected non-transient error to be re-raised")

    error_events = [event for event in logger.events if event[0] == "error"]
    assert len(error_events) == 1
    assert error_events[0][2]["attempt"] == 1
    assert error_events[0][2]["attempt_count"] == 1
    assert error_events[0][2]["account_id"] == "acc-2"
    assert error_events[0][2]["item_id"] == "item-2"


def test_transactions_sync_with_retry_raises_after_max_attempts(monkeypatch):
    module, logger = _load_plaid_sync_module()

    def _transactions_sync(_req):
        raise _PlaidError("PRODUCT_NOT_READY")

    monkeypatch.setattr(module.plaid_client, "transactions_sync", _transactions_sync)
    monkeypatch.setattr(module.time, "sleep", lambda *_a, **_k: None)

    try:
        module._transactions_sync_with_retry(
            req=object(),
            account_id="acc-3",
            item_id="item-3",
            max_attempts=2,
            initial_backoff_seconds=0,
        )
    except _PlaidError as exc:
        assert exc.error_code == "PRODUCT_NOT_READY"
    else:
        raise AssertionError("Expected transient error to be re-raised after retries")

    warning_events = [event for event in logger.events if event[0] == "warning"]
    assert len(warning_events) == 2
    assert warning_events[-1][2]["attempt"] == 2
    assert warning_events[-1][2]["attempt_count"] == 2
    assert warning_events[-1][2]["max_attempts"] == 2
