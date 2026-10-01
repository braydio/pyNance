"""Read and update persistent dashboard LLM settings."""

from __future__ import annotations

from urllib.parse import urlparse

from app.extensions import db
from app.models import LlmSettings

DEFAULT_LLM_SETTINGS_ID = 1


def _serialize(settings: LlmSettings) -> dict[str, object]:
    return {
        "custom_message_enabled": bool(settings.custom_message_enabled),
        "base_url": settings.base_url or "",
    }


def get_llm_settings() -> LlmSettings:
    """Return the singleton LLM settings row, creating it when necessary."""

    settings = db.session.get(LlmSettings, DEFAULT_LLM_SETTINGS_ID)
    if settings is None:
        settings = LlmSettings(id=DEFAULT_LLM_SETTINGS_ID)
        db.session.add(settings)
        db.session.commit()
    return settings


def get_llm_settings_payload() -> dict[str, object]:
    """Return API-safe LLM settings."""

    return _serialize(get_llm_settings())


def _validate_base_url(value: object) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if not isinstance(value, str):
        raise ValueError("base_url must be a string")

    cleaned = value.strip().rstrip("/")
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be a valid http or https URL")
    if parsed.username or parsed.password:
        raise ValueError("base_url must not contain credentials")
    return cleaned


def update_llm_settings(payload: dict[str, object]) -> dict[str, object]:
    """Validate and persist supplied LLM settings fields."""

    settings = get_llm_settings()
    if "custom_message_enabled" in payload:
        enabled = payload["custom_message_enabled"]
        if not isinstance(enabled, bool):
            raise ValueError("custom_message_enabled must be a boolean")
        settings.custom_message_enabled = enabled
    if "base_url" in payload:
        settings.base_url = _validate_base_url(payload["base_url"])

    db.session.commit()
    return _serialize(settings)
