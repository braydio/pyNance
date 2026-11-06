"""Regression tests for explicitly configured local-only dashboard model requests."""

import importlib.util
import sys
import types
from pathlib import Path

BASE_BACKEND = Path(__file__).resolve().parents[1] / "backend"


def _load_status_service(monkeypatch):
    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "app", app_pkg)

    config_stub = types.ModuleType("app.config")
    config_stub.logger = types.SimpleNamespace(warning=lambda *_args, **_kwargs: None)
    monkeypatch.setitem(sys.modules, "app.config", config_stub)

    models_stub = types.ModuleType("app.models")
    models_stub.Account = type("Account", (), {})
    models_stub.Transaction = type("Transaction", (), {})
    models_stub.LlmSettings = type("LlmSettings", (), {})
    monkeypatch.setitem(sys.modules, "app.models", models_stub)

    extensions_stub = types.ModuleType("app.extensions")
    extensions_stub.db = types.SimpleNamespace(session=None)
    monkeypatch.setitem(sys.modules, "app.extensions", extensions_stub)

    services_pkg = types.ModuleType("app.services")
    services_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "app.services", services_pkg)

    settings_path = BASE_BACKEND / "app" / "services" / "llm_settings.py"
    settings_spec = importlib.util.spec_from_file_location("app.services.llm_settings", settings_path)
    settings_module = importlib.util.module_from_spec(settings_spec)
    monkeypatch.setitem(sys.modules, "app.services.llm_settings", settings_module)
    settings_spec.loader.exec_module(settings_module)

    service_path = BASE_BACKEND / "app" / "services" / "dashboard_activity_status.py"
    service_spec = importlib.util.spec_from_file_location("dashboard_activity_status_test_target", service_path)
    service = importlib.util.module_from_spec(service_spec)
    service_spec.loader.exec_module(service)
    return service


def _mock_activity(monkeypatch, service, base_url, enabled=True):
    monkeypatch.setattr(service, "_load_accounts", lambda **_kwargs: [{"balance": 125.0}])
    monkeypatch.setattr(
        service,
        "_load_transactions",
        lambda **_kwargs: [{"amount": -12.0}],
    )
    monkeypatch.setattr(
        service,
        "get_llm_settings",
        lambda: types.SimpleNamespace(custom_message_enabled=enabled, base_url=base_url),
    )


def _reject_request(*_args, **_kwargs):
    raise AssertionError("Unexpected model HTTP request")


def test_blank_url_does_not_make_any_model_request(monkeypatch):
    service = _load_status_service(monkeypatch)
    _mock_activity(monkeypatch, service, base_url=None)
    monkeypatch.setattr(service.requests, "post", _reject_request)

    response = service.generate_activity_status()
    assert response["source"] == "fallback"
    assert response["status_key"] == "largest_expense"


def test_persisted_public_provider_url_is_rejected_before_request(monkeypatch):
    service = _load_status_service(monkeypatch)
    _mock_activity(monkeypatch, service, base_url="https://example.com/v1")
    monkeypatch.setattr(service.requests, "post", _reject_request)

    response = service.generate_activity_status()
    assert response["source"] == "fallback"


def test_local_model_request_has_no_credentials_and_cannot_follow_redirects(monkeypatch):
    service = _load_status_service(monkeypatch)
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return types.SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": '{"status_key":"tip","message":"Check this."}'}}]},
        )

    monkeypatch.setattr(service.requests, "post", fake_post)
    result = service._call_local_model_for_status({"accounts": []}, "http://localhost:11434")
    assert result == {"status_key": "tip", "message": "Check this."}
    assert calls[0][0] == "http://localhost:11434/v1/chat/completions"
    assert calls[0][1]["allow_redirects"] is False
    assert "Authorization" not in calls[0][1]["headers"]
    assert calls[0][1]["json"]["model"]


def test_disabled_model_messaging_never_posts(monkeypatch):
    service = _load_status_service(monkeypatch)
    _mock_activity(monkeypatch, service, base_url="http://localhost:11434", enabled=False)
    monkeypatch.setattr(service.requests, "post", _reject_request)
    assert service.generate_activity_status()["source"] == "fallback"
