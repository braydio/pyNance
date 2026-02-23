"""Helpers for normalizing merchant identity values from transaction payloads."""

from __future__ import annotations

import re
from dataclasses import dataclass

_PREFIX_PATTERNS = [
    re.compile(r"^pos\s+", re.IGNORECASE),
    re.compile(r"^debit\s+", re.IGNORECASE),
    re.compile(r"^purchase\s+", re.IGNORECASE),
    re.compile(r"^sq\s*\*\s*", re.IGNORECASE),
    re.compile(r"^tst\*\s*", re.IGNORECASE),
    re.compile(r"^pp\*\s*", re.IGNORECASE),
    re.compile(r"^paypal\s*\*\s*", re.IGNORECASE),
    re.compile(r"^card\s+\d+\s+", re.IGNORECASE),
]
_TRAILING_NOISE = re.compile(
    r"\b(?:pending|debit|card\s*\d+|ach|online|purchase|pos)\b", re.IGNORECASE
)
_SEPARATOR = re.compile(r"\s*[-:/|]\s*")
_SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class MerchantNormalizationResult:
    """Normalized merchant values used by transaction ingestion.

    Attributes:
        display_name: Canonical merchant display name.
        merchant_slug: Slug derived from ``display_name`` for stable matching.
        source: Source field used to resolve the merchant (``merchant_name``, ``name``,
            ``description``, or ``fallback``).
    """

    display_name: str
    merchant_slug: str
    source: str


def _clean_candidate(value: str) -> str:
    """Remove common processor prefixes and formatting noise from merchant text."""

    cleaned = _SPACES.sub(" ", value or "").strip()
    if not cleaned:
        return ""

    for pattern in _PREFIX_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    cleaned = _SEPARATOR.split(cleaned, maxsplit=1)[0]
    cleaned = _TRAILING_NOISE.sub("", cleaned)
    cleaned = _SPACES.sub(" ", cleaned).strip(" *#-_/.")
    return cleaned


def _to_title_case(value: str) -> str:
    words = []
    for part in value.split():
        if len(part) <= 3 and part.isupper():
            words.append(part)
        else:
            words.append(part.capitalize())
    return " ".join(words)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def resolve_merchant(
    merchant_name: str | None, name: str | None, description: str | None
) -> MerchantNormalizationResult:
    """Resolve merchant identity using fallback order and normalization rules.

    Resolution order:
    1. Plaid ``merchant_name`` when non-empty.
    2. ``name`` field.
    3. ``description`` field.
    4. ``Unknown`` fallback.
    """

    candidates = [
        (merchant_name, "merchant_name"),
        (name, "name"),
        (description, "description"),
    ]

    for candidate, source in candidates:
        cleaned = _clean_candidate(candidate or "")
        if cleaned:
            display_name = _to_title_case(cleaned)
            return MerchantNormalizationResult(
                display_name=display_name,
                merchant_slug=_slugify(display_name),
                source=source,
            )

    return MerchantNormalizationResult(
        display_name="Unknown", merchant_slug="unknown", source="fallback"
    )
