"""Read and update persistent dashboard LLM settings."""

from __future__ import annotations

from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

from app.extensions import db
from app.models import LlmSettings

DEFAULT_LLM_SETTINGS_ID = 1

# Explicit local/overlay ranges, excluding link-local metadata and unspecified hosts.
LOCAL_MODEL_NETWORKS = tuple(
    ip_network(cidr)
    for cidr in (
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "100.64.0.0/10",
        "::1/128",
        "fc00::/7",
    )
)


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
    if parsed.query or parsed.fragment:
        raise ValueError("base_url must not contain query strings or fragments")

    # Financial context must only be sent to locally reachable model servers.
    hostname = parsed.hostname or ""
    try:
        address = ip_address(hostname)
    except ValueError:
        local_host = (
            hostname == "localhost"
            or hostname.endswith((".localhost", ".local", ".internal"))
            or "." not in hostname
        )
    else:
        local_host = any(address in network for network in LOCAL_MODEL_NETWORKS if address.version == network.version)
    if not local_host:
        raise ValueError("base_url must point to a local or private-network model server")
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
