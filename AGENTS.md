# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: Flask application (app factory in `backend/app/__init__.py`), blueprints under `backend/app/routes/`, business logic in `backend/app/services/`, DB setup via `backend/app/extensions.py` and migrations.
- `frontend/`: Vue 3 + Vite app for the UI.
- `tests/`: Pytest suite for API, models, and helpers.
- `scripts/`: Dev utilities (e.g., `scripts/setup.sh`, `scripts/dev-helper.sh`).
- `docs/`: Developer and architecture notes.

## Build, Test, and Development Commands
- Setup (Python venv, tools, hooks): `bash scripts/setup.sh`
- Run backend locally: `python backend/run.py` or `flask --app backend.run run`
- Run frontend locally: `cd frontend && npm run dev`
- Test backend: `pytest -q` (from repo root)
- Lint/format pre-commit suite: `pre-commit run --all-files`

## Coding Style & Naming Conventions
- Python: PEP 8 with type hints. Format with Black (120 cols) and import-order via Isort (black profile).
- Linting: Ruff for fast checks; MyPy for types; Pylint for additional rules; Bandit for security.
- Naming: modules/packages `snake_case`; classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: Pytest; tests live in `tests/` and follow `test_*.py` naming.
- Run focused tests (example): `pytest tests/test_model_field_validation.py -q`.
- Markers: use `@pytest.mark.integration` for tests requiring external services (see `pytest.ini`).
- Aim for coverage on routes, services, and model validation paths.

## Commit & Pull Request Guidelines
- Commits: conventional commits, e.g., `feat(sync): add teller webhook handler`.
- PRs: include description, affected areas (backend/frontend/tests), linked issues, and screenshots for UI changes.
- Before opening a PR: run `pytest`, then `pre-commit run --all-files`. Update docs when API/behavior changes.

## Security & Configuration Tips
- Environment: copy `backend/example.env` to `backend/.env` (never commit secrets). Frontend uses `frontend/.env` similarly.
- Security checks: `bandit -r backend/app/routes` (also enforced via pre-commit).
- Git hooks: repository uses `.githooks` via the setup script; ensure hooks are active for consistent validation.

