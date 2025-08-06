# Contributor guide for short-term agents

This repository has a main goal: to streamline fintech and personal financial data through Python-based agent interfaces.

```
Folders:
- `backend/` - Flask Backend app code, including tellers, plaid, sync)
- `frontend` - Vue 3 + Vite + TypeScript frontend
- `docs` - Documentation sync, Internal tracks for helpers like ChatMpdb
- `scripts` - Useful bash setup scripts
- `tests` - Test suite for api, models, dispatchers
```

## Style Guidelines

- Use PEP 8.1 and beyond, TypeAnnotations
- Docs should match existing deployment types
- Use `lint`, `black`, `ruff` for style
- Run `bash scripts/setup.sh` to prepare the environment (creates `.venv`, installs deps, links hooks)
- Copy `backend/example.env` to `backend/.env` (and `frontend/example.env` to `frontend/.env`)

## Validation

- Python 3.11 is used
- Node 20 required for the frontend
- Run `pytest` from root to validate
- `pre-commit` is configured
- Run `pre-commit run --all-files` before pushing

## Git Hooks

All Git hooks are in `.githooks` and linked by:

```bash
git config core.hooksPath .githooks
```

## PR Expectations

- Title format: `[component] Fix or Add <title>`
- Description must include affected modules (backend/frontend/test)
- If adding API, reflect in docs and add test coverage
- Use `scripts/entr_docsync.sh` if syncing doc updates automatically
- Commit messages: `<type>(<scope>): <description>` (e.g. `feat(auth): add token helper`)

## Agents Should

- Look in `backend/app/` for sync-related logic
- Review `requirements.txt` and `requirements-dev.txt`
- Assume backend is Flask modular app (factory pattern)
- Consider `.nvmrc` and `frontend/package.json` for JS contexts
- Consult `.pre-commit-config.yaml` for formatting enforcement
- Review `docs/index/INDEX.md` for documentation map
- Consult `docs/maintenance/cleanup_checklist.md` for repo organization tasks
- Refer to `docs/ToDoCodex.md` for current dashboard development items

## Migration Areas

- Move deprecated UTC calls to `datetime.now(timezone.utc)`
- Replace usage of `access_token` fields unless declared in models
- Migrate CLI helpers under `app/cli/` to use logger safely

## Testing Checklist

- ✅ `pytest`
- ✅ `pre-commit run --all-files`
- ✅ Add tests for API or dispatcher behavior
- ✅ Validate test_model_fields_are_valid does not fail

---

This guide exists to help agents operate predictably and reduce context churn.

If a test fails, check test structure before code.
If docs are out of sync, run `entr_docsync.sh` or `auto_docsync.sh`.
If you update sync behavior, please update CLI and add to coverage.
