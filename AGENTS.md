# Repository Guidelines

## Project Structure & Module Organization

- `backend/` hosts the Flask API; the app factory lives in `backend/app/__init__.py`, routes in `app/routes/`, and business logic in `app/services/`. Shared extensions and database setup sit in `backend/app/extensions.py`, with Alembic migrations alongside `backend/app/`.
- `frontend/` contains the Vue 3 client following script-setup conventions. Keep UI assets and components scoped within this directory.
- `tests/` holds the pytest suite; fixtures belong in `tests/conftest.py`. Automation scripts stay under `scripts/`, while architecture notes live in `docs/`.

## Build, Test, and Development Commands

- `bash scripts/setup.sh` boots Python virtualenvs, installs npm dependencies, and configures git hooks.
- `python backend/run.py` (or `flask --app backend.run run`) starts the API with hot reload.
- `cd frontend && npm run dev` runs the Vue development server.
- `pytest -q` executes backend tests; narrow scope with `pytest tests/test_<feature>.py -q`.
- `pre-commit run --all-files` runs Black, Ruff, Isort, MyPy, Pylint, and Bandit before committing.

## Coding Style & Naming Conventions

- Follow PEP 8 with 120-character lines enforced by Black; organize imports with Isort (Black profile).
- Use `snake_case` for variables and functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Vue components should avoid wrapping `<draggable>` in `<Transition>`; leverage script-setup syntax.

## Testing Guidelines

- Write pytest cases for every new route, service, or constraint; include both success and failure paths.
- Name files `tests/test_<feature>.py`; mark long-running specs with `@pytest.mark.integration`.
- Prefer fixtures in `tests/conftest.py` for shared setup and keep assertions focused on observable behavior.

## Commit & Pull Request Guidelines

- Use Conventional Commits (e.g., `feat(sync): add teller webhook handler`) with focused scopes.
- PRs should summarize changes, flag affected areas (backend/frontend/tests), link related issues, and attach UI screenshots when applicable.
- Run `pytest` and `pre-commit run --all-files` before opening a PR; update `docs/` when public behavior changes.

## Security & Configuration Tips

- Copy `backend/example.env` to `backend/.env` (and `frontend/.env` as needed); never commit secrets.
- Run `bandit -r backend/app/routes` regularly and treat findings as blockers.
- Handle optional API responses defensively; wrap setup-time calls in try/except or `Promise.allSettled` and provide safe fallbacks.
