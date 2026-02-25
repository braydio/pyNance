# `category_canonical.py`

## Purpose

Normalize heterogeneous Plaid category inputs into canonical category contracts:

- `category_slug`: stable internal key for storage and analytics grouping.
- `category_display`: user-facing label for API/UI payloads.

## Key APIs

- `canonicalize_category(primary, detailed, pfc_primary, pfc_detailed)`
  - Produces canonical `(slug, display)` from legacy category paths and PFC enums.
- `canonical_display_for_slug(slug, fallback_display=None)`
  - Builds deterministic display labels from canonical slugs when only the key is available.

## Notes

- The helper preserves compatibility with older legacy category strings while
  promoting canonical PFC detailed enums when present.
- Unknown values normalize to `UNKNOWN` / `Unknown`.
