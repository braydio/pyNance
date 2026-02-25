# Category Model

## Purpose

`Category` stores canonical transaction category identity while preserving source
provenance from Plaid legacy paths and personal-finance-category (PFC) enums.

## Core Fields

- `id`: Integer primary key.
- `category_slug`: Stable internal key (e.g., `FOOD_AND_DRINK_COFFEE`) used for
  grouping and deduplication.
- `category_display`: UI label derived from the canonical slug (e.g.,
  `Food and Drink - Coffee`).
- `primary_category`, `detailed_category`: Legacy Plaid category path values.
- `pfc_primary`, `pfc_detailed`, `pfc_icon_url`: Raw PFC values retained for
  provenance and display assets.
- `parent_id`: Optional hierarchical parent relationship.

## Behaviors

- Category resolution is canonical-slug-first via
  `app.sql.account_logic.get_or_create_category`.
- Legacy category strings and PFC enum variants map into a single canonical
  category row whenever their normalized slug matches.
