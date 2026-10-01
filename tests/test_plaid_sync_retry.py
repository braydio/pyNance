"""Unit tests for Plaid sync retry handling."""

import importlib.util
import os
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
    """Load the service without replacing shared app modules in sys.modules."""
    module_path = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "services", "plaid_sync.py")
    spec = importlib.util.spec_from_file_location("plaid_sync_retry_test", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    logger = _DummyLogger()
    module.logger = logger
    module.plaid_client = types.SimpleNamespace(transactions_sync=lambda _req: None)
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
