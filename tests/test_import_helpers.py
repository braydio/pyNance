"""Tests for import helper utilities with stubbed dependencies."""

import importlib.util
import os
import sys
import types

# Stub minimal app.config with logger
app_stub = types.ModuleType("app")
config_stub = types.ModuleType("app.config")


class DummyLogger:
    """Collect log messages emitted during tests.

    Attributes:
        messages: Sequence of captured log entries for assertion.
    """

    def __init__(self):
        """Initialise an in-memory store for log messages."""
        self.messages = []

    def _record(self, level, *args, **kwargs):
        """Save a log record for later assertions.

        Args:
            level: The string level for the log (for example, ``"info"``).
            *args: Positional arguments that were provided to the logger call.
            **kwargs: Keyword arguments that accompanied the logger call.
        """

        self.messages.append((level, args, kwargs))

    def debug(self, *args, **kwargs):
        """Capture debug level log messages without side effects.

        Args:
            *args: Positional arguments that were provided to ``logger.debug``.
            **kwargs: Keyword arguments that accompanied the call.
        """

        self._record("debug", *args, **kwargs)

    def info(self, *args, **kwargs):
        """Capture info level log messages without side effects.

        Args:
            *args: Positional arguments that were provided to ``logger.info``.
            **kwargs: Keyword arguments that accompanied the call.
        """

        self._record("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        """Capture warning level log messages without side effects.

        Args:
            *args: Positional arguments that were provided to ``logger.warning``.
            **kwargs: Keyword arguments that accompanied the call.
        """

        self._record("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        """Capture error level log messages without side effects.

        Args:
            *args: Positional arguments that were provided to ``logger.error``.
            **kwargs: Keyword arguments that accompanied the call.
        """

        self._record("error", *args, **kwargs)


config_stub.logger = DummyLogger()
sys.modules.setdefault("app", app_stub)
sys.modules["app.config"] = config_stub

MODULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "backend", "app", "helpers", "import_helpers.py"
)
spec = importlib.util.spec_from_file_location("import_helpers", MODULE_PATH)
import_helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_helpers)


def test_import_transactions_from_pdf():
    pdf_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "synchrony_sample.pdf"
    )
    result = import_helpers.import_transactions_from_pdf(pdf_path)
    assert result["status"] == "success"
    assert result["count"] == 3
    first = result["data"][0]
    assert first["name"] == "Amazon Purchase"
    assert first["type"] == "debit"
