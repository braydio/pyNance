# Repository Guidelines

Use this guide to keep contributions consistent with the project's structure, tooling, and review standards.

## Project Structure & Module Organization
- `backend/app/` contains the Flask app factory, HTTP routes in `app/routes/`, and services in `app/services/`; shared extensions live in `app/extensions.py`, with Alembic migrations under `backend/migrations/versions/`.
- `frontend/` holds the Vue 3 client (script-setup) along with scoped components, stores, and assets.
- `tests/` stores the pytest suite and fixtures (`tests/conftest.py`); automation scripts sit in `scripts/`, while long-form docs live in `docs/`.

## Build, Test, and Development Commands
- `bash scripts/setup.sh` provisions Python/Node environments, installs dependencies, and wires git hooks.
- `python backend/run.py` or `flask --app backend.run run` serves the API with hot reload.
- `cd frontend && npm run dev` starts the Vue dev server.
- `pytest -q` executes backend tests; scope with `pytest tests/test_<feature>.py -q` when iterating.
- `pre-commit run --all-files` runs Black, Ruff, Isort, MyPy, Pylint, and Bandit.

## Coding Style & Naming Conventions
- Follow Black's 120-character formatting; use Isort (Black profile) for imports and Ruff for linting.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Vue files lean on script-setup; do not wrap `<draggable>` in `<Transition>`.

## Testing Guidelines
- Cover every new route, service, or migration with pytest, including success and failure paths.
- Name files `tests/test_<feature>.py`, tag long jobs with `@pytest.mark.integration`, and prefer shared fixtures for setup.

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat(sync): add teller webhook handler`) with focused scopes.
- PRs should summarize impact, flag affected surfaces (backend/frontend/tests), link issues, and include relevant UI captures.
- Run `pytest` and `pre-commit run --all-files` before requesting review; update `docs/` when behavior changes.

## Security & Configuration Tips
- Copy `backend/example.env` to `backend/.env` (and `frontend/.env` if needed); never commit secrets.
- Run `bandit -r backend/app/routes` regularly and treat hits as blockers.
- Guard optional API responses with try/except or `Promise.allSettled`, providing safe fallbacks across services and UI flows.
