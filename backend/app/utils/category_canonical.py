"""Canonical category normalization helpers.

These helpers collapse legacy Plaid category labels and PFC enum values into a
stable internal category slug plus a UI-friendly display label.
"""

from __future__ import annotations

import re

from app.utils.category_display import category_display, humanize_enum, strip_parent

UNKNOWN_SLUG = "UNKNOWN"
UNKNOWN_DISPLAY = "Unknown"


def _normalize_slug_component(value: str | None) -> str:
    """Convert a category component into uppercase underscore form."""

    if not value:
        return ""
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized.upper()


def canonicalize_category(
    primary: str | None,
    detailed: str | None,
    pfc_primary: str | None,
    pfc_detailed: str | None,
) -> tuple[str, str]:
    """Return canonical ``(category_slug, category_display)`` values.

    Args:
        primary: Legacy Plaid primary category (human-readable in many payloads).
        detailed: Legacy Plaid detailed category.
        pfc_primary: Plaid PFC primary enum.
        pfc_detailed: Plaid PFC detailed enum.

    Returns:
        Tuple of stable slug and display label.
    """

    normalized_pfc_primary = _normalize_slug_component(pfc_primary)
    normalized_pfc_detailed = _normalize_slug_component(pfc_detailed)

    if normalized_pfc_detailed and normalized_pfc_detailed != UNKNOWN_SLUG:
        slug = normalized_pfc_detailed
        display = category_display(normalized_pfc_primary or UNKNOWN_SLUG, slug)
        return slug, display

    legacy_primary = _normalize_slug_component(primary)
    legacy_detailed = _normalize_slug_component(detailed)

    if legacy_detailed and legacy_detailed != UNKNOWN_SLUG:
        if legacy_primary and not legacy_detailed.startswith(f"{legacy_primary}_"):
            slug = f"{legacy_primary}_{legacy_detailed}"
        else:
            slug = legacy_detailed

        if legacy_primary and legacy_primary != UNKNOWN_SLUG:
            display = category_display(legacy_primary, slug)
        else:
            display = humanize_enum(slug)
        return slug, display

    if legacy_primary and legacy_primary != UNKNOWN_SLUG:
        return legacy_primary, humanize_enum(legacy_primary)

    return UNKNOWN_SLUG, UNKNOWN_DISPLAY


def canonical_display_for_slug(
    slug: str | None, fallback_display: str | None = None
) -> str:
    """Build a deterministic display label for a canonical category slug."""

    normalized_slug = _normalize_slug_component(slug)
    if not normalized_slug:
        return fallback_display or UNKNOWN_DISPLAY

    if not fallback_display:
        return humanize_enum(normalized_slug)

    # If the fallback already contains a split label, trust it for readability.
    if " - " in fallback_display:
        return fallback_display

    primary_slug = _normalize_slug_component(fallback_display)
    if primary_slug and normalized_slug.startswith(f"{primary_slug}_"):
        detailed_slug = strip_parent(normalized_slug, primary_slug)
        return category_display(primary_slug, detailed_slug)

    return fallback_display
