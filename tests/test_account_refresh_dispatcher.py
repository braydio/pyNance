"""Tests for account refresh dispatcher logic."""

import importlib.util
import os
import sys
import types
from datetime import datetime, timedelta, timezone

# Stub minimal app modules required by account_refresh_dispatcher
app_stub = types.ModuleType("app")
config_stub = types.ModuleType("app.config")
models_stub = types.ModuleType("app.models")
services_stub = types.ModuleType("app.services")


class DummyLogger:
    """Minimal logger stub for tests."""

    def debug(self, *a, **k):
        """Ignore debug messages."""

    def info(self, *a, **k):
        """Ignore info messages."""

    def warning(self, *a, **k):
        """Ignore warnings."""

    def error(self, *a, **k):
        """Ignore errors."""


config_stub.logger = DummyLogger()
models_stub.Account = object
models_stub.db = types.SimpleNamespace()
services_stub.sync_service = types.SimpleNamespace()

sys.modules.setdefault("app", app_stub)
sys.modules["app.config"] = config_stub
sys.modules["app.models"] = models_stub
sys.modules["app.services"] = services_stub

MODULE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "backend",
    "app",
    "helpers",
    "account_refresh_dispatcher.py",
)
spec = importlib.util.spec_from_file_location("account_refresh_dispatcher", MODULE_PATH)
account_refresh_dispatcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(account_refresh_dispatcher)


def test_is_due_handles_date_and_datetime():
    now = datetime.now(timezone.utc)
    three_days_ago = now - timedelta(days=3)

    # Should be due when last_synced is a datetime in the past
    assert account_refresh_dispatcher.is_due(three_days_ago, "plaid")

    # Should also handle date objects without error
    assert account_refresh_dispatcher.is_due(three_days_ago.date(), "plaid")

    # A recent date should not be due
    assert not account_refresh_dispatcher.is_due(now.date(), "plaid")
