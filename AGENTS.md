# Repository Guidelines

Use this guide to keep contributions consistent with the project's structure, tooling, and review standards.

## Task Packet System (Authoritative)

Executable implementation task packets live only under `docs/task-packets/`.

Canonical control files:

- `docs/task-packets/README.md` – naming, lifecycle, execution flow, and authoring standard.
- `docs/task-packets/INDEX.md` – canonical discovery index for every packet.
- `docs/task-packets/TRACKER.md` – live execution state, priority, dependencies, and blockers.
- `docs/task-packets/active/` – Draft, Ready, In Progress, and Blocked packets.
- `docs/task-packets/completed/` – Complete packets.
- `docs/task-packets/archived/` – Superseded or Cancelled packets.

Packet filenames use the immutable convention:

```text
TP-YYYYMMDD-NNN-kebab-case-slug.md
```

Do not create new executable task packets in `docs/devnotes/` or arbitrary feature folders. Legacy files there may be compatibility pointers only.

### Agent execution flow

When asked to implement or continue a task packet:

1. Read this `AGENTS.md`.
2. Read `docs/task-packets/README.md`.
3. Check `docs/task-packets/TRACKER.md`.
4. Resolve the Packet ID through `docs/task-packets/INDEX.md` and open only its canonical file.
5. Validate the named files/symbols against current `main`; do not perform repo-wide rediscovery unless the packet is demonstrably stale.
6. Mark the packet and tracker `In Progress` when implementation begins.
7. Follow the packet's implementation order, non-goals, tests, and acceptance criteria.
8. If blocked, record the exact blocker and resume condition in the tracker.
9. On completion, set Status to `Complete`, move the packet to `completed/`, and update the index/tracker in the same change.

Never implement from a legacy pointer file when a canonical packet exists.

### Task packet authoring rules

These rules apply to any agent, including ChatGPT/Codex, writing or revising packets for this repository:

- Inspect current `main` before writing the packet.
- Use exact repository-relative file paths.
- Name the exact functions, classes, routes, components, models, migrations, and tests involved.
- Include current code excerpts and concrete replacement code/pseudocode when practical.
- Prefer symbol names over fragile line numbers; line numbers may be secondary hints only.
- Resolve architecture decisions before handoff when the repository already provides enough evidence.
- Reuse existing helpers/contracts instead of inventing parallel systems.
- Include an explicit implementation order, focused tests, validation commands, acceptance criteria, non-goals, and completion-report requirements.
- State dependencies, locks, and an expected packet count/order when work is split across multiple packets.
- Keep one packet to one coherent, independently testable workstream.
- Add `Do not rediscover` boundaries when the relevant surface has already been traced.
- Minimize token burn: prefer exact paths + real code recommendations over exploratory prose.
- When runtime evidence changes the diagnosis, update the canonical packet directly, bump `Last updated`, and update the tracker. Do not leave the correction only in chat or a side note.
- Do not broaden a packet with opportunistic cleanup unrelated to its acceptance criteria.

## Project Structure & Module Organization

- `backend/app/` contains the Flask app factory, HTTP routes in `app/routes/`, and services in `app/services/`; shared extensions live in `app/extensions.py`, with Alembic migrations under `backend/migrations/versions/`.
- `frontend/` holds the Vue 3 client (script-setup) along with scoped components, stores, and assets.
- `tests/` stores the pytest suite and fixtures (`tests/conftest.py`); automation scripts sit in `scripts/`, while long-form docs live in `docs/`.
- Documentation lives in Markdown under `docs/` and mirrors the backend layout (for example `docs/backend/app/` maps to `backend/app/`).
- Architecture notes live in `docs/architecture/`, workflows in `docs/process/`, working notes in `docs/devnotes/`, and executable implementation packets in `docs/task-packets/`.
- When adding backend modules, create the matching docs in `docs/backend/` and update the nearest index.

## Build, Test, and Development Commands

- `bash scripts/setup.sh` provisions Python/Node environments, installs dependencies, and wires git hooks.
- `python backend/run.py` or `flask --app backend.run run` serves the API with hot reload.
- `cd frontend && npm run dev` starts the Vue dev server.
- `pytest -q` executes backend tests; scope with `pytest tests/test_<feature>.py -q` when iterating.
- `pre-commit run --all-files` runs Black, Ruff, MyPy, Pylint, and Bandit.
- Configure `SQLALCHEMY_DATABASE_URI` for PostgreSQL and apply migrations with `flask db upgrade` before running the API.

## Coding Style & Naming Conventions

- Follow Black's 120-character formatting; use Ruff for linting and import sorting.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Vue files lean on script-setup; do not wrap `<draggable>` in `<Transition>`.
- Review the relevant docs in `docs/` for best practices before changing behavior.

## Testing Guidelines

- Cover every new route, service, or migration with pytest, including success and failure paths.
- Name files `tests/test_<feature>.py`, tag long jobs with `@pytest.mark.integration`, and prefer shared fixtures for setup.

## Commit & Pull Request Guidelines

- Use Conventional Commits (e.g., `feat(sync): add plaid webhook handler`) with focused scopes.
- PRs should summarize impact, flag affected surfaces (backend/frontend/tests), link issues, and include relevant UI captures.
- Run `pytest` and `pre-commit run --all-files` before requesting review; update `docs/` when behavior changes.

## Security & Configuration Tips

- Copy `backend/example.env` to `backend/.env` (and `frontend/.env` if needed); never commit secrets.
- Run `bandit -r backend/app/routes` regularly and treat hits as blockers.
- Guard optional API responses with try/except or `Promise.allSettled`, providing safe fallbacks across services and UI flows.

## Visual Design Policy

- Do not make visual updates unless the user explicitly requests them; rely on documentation for any approved styling rules.
- Current visual design guidelines for dashboard charts and similar components live in `docs/devnotes/` (for example `docs/devnotes/daily-net-chart.md` documents the Daily Net chart’s stacking, net indicator, tooltip, legend, trendline, and overlay behavior).
