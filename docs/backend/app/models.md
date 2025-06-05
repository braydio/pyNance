## 📘 `models.py`
```markdown
# Database Models

Defines the SQLAlchemy models for the application including `Account`,
`PlaidAccount`, `TellerAccount`, `AccountHistory`, `Transaction`, and related
entities. Mixes in timestamp columns and sets up relationships used throughout
services and routes.

**Dependencies**: `flask_sqlalchemy` via `app.extensions.db`.
```
