# Repository Guidelines

## Project Structure & Module Organization
- `backend/app/` houses the Flask factory, routes (`app/routes/`), and service layer (`app/services/`); shared extensions live in `app/extensions.py`.
- `backend/migrations/versions/` stores Alembic revisions, while `scripts/` holds automation helpers.
- `frontend/` contains the Vue 3 client with script-setup components, scoped styles, stores, and assets.
- Tests and fixtures live in `tests/`, and reference docs belong in `docs/`.

## Build, Test, and Development Commands
- `bash scripts/setup.sh` – installs Python/Node deps, configures hooks, and primes environments.
- `python backend/run.py` or `flask --app backend.run run` – launches the API with reloading; set `SQLALCHEMY_DATABASE_URI` first.
- `cd frontend && npm run dev` – starts the Vue dev server alongside the API.
- `pytest -q` – runs the backend test suite; narrow with `pytest tests/test_<feature>.py -q`.
- `pre-commit run --all-files` – executes Black, Ruff, Isort, MyPy, Pylint, and Bandit gates before review.

## Coding Style & Naming Conventions
- Python follows Black (120-char limit) and Isort (Black profile); lint with Ruff.
- Naming: `snake_case` functions/vars, `PascalCase` classes, and `UPPER_SNAKE_CASE` constants.
- Vue components use `<script setup>` with scoped styles; never wrap `<draggable>` in `<Transition>`.
- Keep comments purposeful and favor defensive checks around optional integrations.

## Testing Guidelines
- Use pytest with fixtures from `tests/conftest.py`; mark long-running cases with `@pytest.mark.integration`.
- Create files as `tests/test_<feature>.py` covering success and failure paths for every route, service, or migration.
- Run `pytest -q` locally and ensure new tests remain deterministic and side-effect free.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (e.g., `feat(sync): add plaid webhook handler`) focused on a single scope.
- PRs must summarize impact, call out affected surfaces (backend/frontend/tests), link issues, and include UI captures when relevant.
- Confirm `pytest` and `pre-commit run --all-files` succeed before requesting review; mention any skipped checks explicitly.

## Security & Configuration Tips
- Copy `backend/example.env` to `backend/.env` (and frontend equivalents) without committing secrets.
- Run `bandit -r backend/app/routes` regularly and treat findings as blockers.
- Guard optional API responses with try/except or UI fallbacks (`Promise.allSettled`) to prevent cascading failures.
