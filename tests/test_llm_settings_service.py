"""Unit tests for persistent LLM setting validation and updates."""

import importlib.util
import os
import sys
import types

import pytest

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
app_pkg = types.ModuleType("app")
app_pkg.__path__ = []
sys.modules["app"] = app_pkg
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(session=None)
sys.modules["app.extensions"] = extensions_stub
models_stub = types.ModuleType("app.models")
models_stub.LlmSettings = type("LlmSettings", (), {})
sys.modules["app.models"] = models_stub

SERVICE_PATH = os.path.join(BASE_BACKEND, "app", "services", "llm_settings.py")
spec = importlib.util.spec_from_file_location("llm_settings_service", SERVICE_PATH)
llm_settings_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_settings_service)


def _configure_existing(monkeypatch):
    existing = types.SimpleNamespace(custom_message_enabled=True, base_url=None)
    commits = []
    session = types.SimpleNamespace(get=lambda *_args: existing, commit=lambda: commits.append(True))
    monkeypatch.setattr(llm_settings_service, "db", types.SimpleNamespace(session=session))
    return existing, commits


def test_update_accepts_ollama_host(monkeypatch):
    existing, commits = _configure_existing(monkeypatch)
    payload = llm_settings_service.update_llm_settings(
        {"custom_message_enabled": False, "base_url": "http://localhost:11434/"}
    )
    assert payload == {"custom_message_enabled": False, "base_url": "http://localhost:11434"}
    assert existing.custom_message_enabled is False
    assert commits


@pytest.mark.parametrize("url", ["localhost:11434", "file:///tmp/socket", "https://user:pass@example.com"])
def test_update_rejects_invalid_or_credentialed_urls(monkeypatch, url):
    _configure_existing(monkeypatch)
    with pytest.raises(ValueError, match="base_url"):
        llm_settings_service.update_llm_settings({"base_url": url})
