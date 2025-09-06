"""Tests for the ENABLE_ARBIT_DASHBOARD configuration flag."""

import importlib
import os
import sys

from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)


def reload_config():
    """Reload configuration modules to pick up environment changes."""
    sys.modules.pop("app.config.environment", None)
    sys.modules.pop("app.config", None)
    import app.config as config
    import app.config.environment  # noqa: F401  # re-import to apply env vars

    importlib.reload(config)
    return config


def test_default_disabled(monkeypatch):
    """Flag defaults to False when the environment variable is unset."""
    monkeypatch.delenv("ENABLE_ARBIT_DASHBOARD", raising=False)
    reload_config()
    app = Flask(__name__)
    app.config.from_object("app.config")
    assert app.config["ENABLE_ARBIT_DASHBOARD"] is False


def test_override_enabled(monkeypatch):
    """Flag is True when the environment variable is truthy."""
    monkeypatch.setenv("ENABLE_ARBIT_DASHBOARD", "true")
    reload_config()
    app = Flask(__name__)
    app.config.from_object("app.config")
    assert app.config["ENABLE_ARBIT_DASHBOARD"] is True
