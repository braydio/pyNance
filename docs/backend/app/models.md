# Database Models - Core SQLAlchemy Schema [DB_MODELS]

This document defines the core database models for the pyNance application, including account entities, transaction records, and relationship mappings used throughout the backend services and API routes.

## Database Models Overview [MODELS_OVERVIEW]

Defines the SQLAlchemy models for the application including `Account`, `PlaidAccount`, `TellerAccount`, `AccountHistory`, `Transaction`, and related entities. Mixes in timestamp columns and sets up relationships used throughout services and routes.

### Dependencies
- `flask_sqlalchemy` via `app.extensions.db`
- Timestamp mixins for created/updated fields
- Relationship mappings for foreign key constraints

### Key Models
- **Account**: Core account entity with provider-agnostic fields
- **PlaidAccount**: Plaid-specific account extensions
- **TellerAccount**: Teller-specific account extensions  
- **Transaction**: Universal transaction records across all providers
- **AccountHistory**: Historical balance snapshots
- **Category**: Transaction categorization taxonomy
