# pyNance/backend/CLAUDE.md

---

## Core Conventions

- **Config:**

  - Put all secrets, API keys, and environment-sensitive logic in `config/`
  - Typical files: `environment.py`, `constants.py`, `plaid_config.py`, `log_setup.py`
  - Do **not** hardcode secrets anywhere else!
  - Use `.env` for local development keys (not committed)

- **Models:**

  - All DB schema/models in `models.py` (single-file style)
  - Use type hints, docstrings, and keep models DRY
  - Foreign key relationships and constraints should be explicit

- **Routes:**

  - API endpoints are organized in `routes/` (by resource/domain: transactions, accounts, etc.)
  - Prefer blueprints (Flask) or APIRouter (FastAPI) for modularity
  - Route naming: `/api/resource` or `/api/v1/resource`

- **Helpers/Utils:**

  - Place reusable code for business logic, data validation, or format transforms in `helpers/`
  - Shared functions not tied to business logic go in `utils/`

- **Services:**

  - Any code that wraps a third-party API (Plaid, Teller, etc.) lives in `services/`
  - Also for internal logic that crosses route boundaries (accounting, reconciliation, etc.)

- **CLI:**

  - For scripts and utilities intended for CLI use (DB setup, admin tasks)
  - Use Click or Typer for new scripts

- **Static/Certs/SQL:**
  - `static/`: rarely touched except for serving static assets
  - `certs/`: SSL files, leave unchanged unless working on HTTPS setup
  - `sql/`: migration scripts or complex SQL not handled by ORM

---

## How to Make Changes

- **New API Route:**

  - Create new file in `routes/` or add endpoint to relevant route file
  - Register blueprint/APIRouter in app entrypoint (`__init__.py`)
  - Add validation/helpers as needed in `helpers/`
  - Update/add models if new DB entities are needed

- **Update Config:**

  - Edit files in `config/`, not in main codebase
  - Document new environment variables at the top of the relevant config file

- **Add Helper or Utility:**

  - Use `helpers/` for business logic, `utils/` for general-purpose functions
  - Add tests as needed

- **Edit Models:**
  - Edit `models.py` (ensure migrations are up-to-date if using Alembic or raw SQL)
  - Use type hints and docstrings

---

## Project Security & Secrets

- **Never commit real API keys, secrets, or private certs**
- Store these in `.env` or `config/` (as template/example only)
- Code AI: If you see a placeholder, **do not replace with a real key**

---

## Testing & Development

- Tests should target core helpers, models, and routes
- Use `pytest` for Python testing
- Add coverage for new logic when practical
- To run backend (example):
  ```sh
  cd backend
  source .venv/bin/activate
  export $(cat .env | xargs)
  flask run --app app
  ```
