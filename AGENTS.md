# Repository Guidelines

## Project Structure & Module Organization

The Flask backend lives in `backend/`, with the app factory at `backend/app/__init__.py`, HTTP blueprints under `app/routes/`, and business logic in `app/services/`. Shared extensions and database setup are defined in `backend/app/extensions.py`, while migrations sit beside the backend package. The Vue 3 client resides in `frontend/`, and `tests/` contains the pytest suite. Supporting materials stay in `scripts/` for automation and `docs/` for architecture notes.

## Build, Test, and Development Commands

- `bash scripts/setup.sh` — bootstrap Python envs, npm packages, and git hooks after cloning.
- `python backend/run.py` or `flask --app backend.run run` — start the API with hot reload.
- `cd frontend && npm run dev` — run the Vue dev server.
- `pytest -q` or `pytest tests/test_<module>.py -q` — execute the backend test suite.
- `pre-commit run --all-files` — apply Black, Ruff, Isort, MyPy, Pylint, and Bandit checks.

## Coding Style & Naming Conventions

Use PEP 8 with type hints and Black’s 120-column profile; organize imports via Isort’s Black profile. Ruff, MyPy, Pylint, and Bandit are enforced by pre-commit—address warnings rather than suppressing them. Name modules, functions, and variables with `snake_case`, classes with `PascalCase`, and constants with `UPPER_SNAKE_CASE`. Vue components should follow script-setup patterns and let vuedraggable manage transitions without wrapping `<draggable>` in `<Transition>`.

## Testing Guidelines

Write pytest cases for every new route, service, or model constraint. Keep tests under `tests/` and name files `test_<feature>.py`; prefer descriptive fixtures in `tests/conftest.py`. Tag long-running or external-service specs with `@pytest.mark.integration`, and include both success and failure scenarios.

## Commit & Pull Request Guidelines

Adopt Conventional Commits (e.g., `feat(sync): add teller webhook handler`) and keep commits focused. PRs should summarize changes, flag affected areas (backend/frontend/tests), link related issues, and attach UI screenshots when applicable. Run `pytest` and `pre-commit run --all-files` before requesting review, and update `docs/` when public behavior shifts.

## Security & Configuration Tips

Copy `backend/example.env` to `backend/.env` (and `frontend/.env` for the client) without committing secrets. Run `bandit -r backend/app/routes` regularly; treat Bandit findings as blockers. Handle optional or experimental API responses defensively—wrap setup-time requests in try/catch or `Promise.allSettled` and provide sensible UI fallbacks.
