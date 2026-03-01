---
Owner: Backend Team
Last Updated: 2026-02-28
Status: Active
---

# Database Models - Core SQLAlchemy Schema [DB_MODELS]

This document defines the core database models for the pyNance application, including account entities, transaction records, and relationship mappings used throughout the backend services and API routes.

## Database Models Overview [MODELS_OVERVIEW]

Defines the SQLAlchemy models for the application including `Account`, `PlaidAccount`, `AccountHistory`, `Transaction`, and related entities. Mixes in timestamp columns and sets up relationships used throughout services and routes.

### Dependencies

- `flask_sqlalchemy` via `app.extensions.db`
- Timestamp mixins for created/updated fields (`backend/app/models/mixins.py`)
- Relationship mappings for foreign key constraints

### Key Models

- **Account**: Core account entity with provider-agnostic fields, including a canonical computed `display_name` derived from institution + subtype/type (and optional masked suffix when available) while preserving raw `name` as the editable source value.
- **Investment flags on Account**: `is_investment`, `investment_has_holdings`, `investment_has_transactions`, and `product_provenance` are persisted explicitly so routes can serialize deterministic investment semantics without inferring from free-form strings.
- **PlaidAccount**: Plaid-specific account extensions
- **Transaction**: Universal transaction records across all providers
- **AccountHistory**: Historical balance snapshots
- **Category**: Transaction categorization taxonomy
- **Category canonicalization**: Categories include a stable `category_slug` plus
  `category_display`, while preserving raw Plaid legacy and PFC fields for
  provenance.
- **Tag**: User-defined labels tied to transactions; names are unique per user and default to `#untagged` in serialization when no tags exist.
