# TP-20261007-001: Local Schema Head Activation + Safe-to-Spend Migration Guard

**Packet ID:** TP-20261007-001  
**Status:** Blocked
**Created:** 2026-10-07  
**Last updated:** 2026-10-08
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261007-001-local-schema-head-activation.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261002-001 (Complete)  
**Priority:** High, runtime-blocking  
**Expected packet count:** 1  

## Objective

Eliminate the current local Safe-to-Spend crash by applying the already-shipped planning-schema reconciliation migration to the active database, then close the local-development startup gap that allowed application code to run against an older Alembic revision.

The required result is:

1. the active local database is upgraded through `f84c6e2a91b7`;
2. `planned_bills.frequency`, `planned_bills.origin`, and `planned_bills.account_id` exist before Safe-to-Spend is served;
3. normal local startup cannot silently serve the app against pending Alembic migrations;
4. no duplicate planning migration and no ORM/query workaround is introduced.

## Runtime evidence

At 2026-10-07 02:50 EDT the running local backend fails in:

- `backend/app/routes/dashboard.py::get_safe_to_spend`
- `backend/app/services/safe_to_spend.py::_upcoming_bill_payload`

with:

```text
psycopg.errors.UndefinedColumn:
column planned_bills.frequency does not exist
```

The generated ORM query selects `planned_bills.frequency`, which is part of the current `PlannedBill` model.

## Confirmed current state on main

### Model

File: `backend/app/models/planning_models.py`  
Class: `PlannedBill`

Current model includes:

```python
frequency = db.Column(db.String(20), nullable=False, default="monthly")
origin = db.Column(db.String(20), nullable=False, default="manual")
account_id = db.Column(db.String(128), nullable=True, index=True)
```

Do not remove or make these fields optional to mask schema drift.

### Reconciliation migration already exists

File: `backend/migrations/versions/f84c6e2a91b7_reconcile_legacy_planning_schema.py`

Revision:

```python
revision = "f84c6e2a91b7"
down_revision = "e6a9c2f4b8d1"
```

Its `upgrade()` already adds the missing legacy columns and indexes idempotently:

- `planning_scenarios.account_id`
- `planning_scenarios.planning_balance_cents`
- `planning_scenarios.currency_code`
- `planned_bills.frequency`
- `planned_bills.origin`
- `planned_bills.account_id`
- `ix_planning_scenarios_account_id`
- `ix_planned_bills_account_id`

The migration already has focused coverage in:

- `tests/test_planning_schema_migration.py`

### Deployment paths already apply migrations

- `backend/docker-entrypoint.sh` runs `flask --app 'app:create_app' db upgrade`.
- `render.yaml` runs the same upgrade before Gunicorn.
- `backend/scripts/setup.sh` runs migrations during initial local setup.

### Local direct-run path does not

File: `backend/run.py`

Current:

```python
def main() -> None:
    app = create_app()
    app.run(host="0.0.0.0", static_files="static", port=5000, debug=True)
```

A developer who already ran setup can pull new migrations and continue using `python backend/run.py` without ever advancing the database. That is the gap exposed by the current failure.

### Documentation currently encourages the wrong pull/update flow

The root `README.md` section "Database Migrations" currently says to run both:

```bash
flask --app backend.run db migrate -m "update schema"
flask --app backend.run db upgrade
```

Running `db migrate` after merely pulling schema changes is incorrect. It generates a new revision rather than applying the existing repository revisions and can create spurious migration files. This guidance must be corrected.

### Local target verification, 2026-10-08

The configured database reported `ENV=production` and target `pynance:public`. Read-only Alembic inspection found current revision `e6a9c2f4b8d1` and repository head `f84c6e2a91b7`. Read-only schema inspection confirmed `planned_bills.frequency`, `planned_bills.origin`, and `planned_bills.account_id` are absent. The `db upgrade` command was not run because this configured target is production, not a confirmed local development database.

**Blocker:** The local development database target is not configured in this environment; the only configured target is production.

**Resume when:** Configure `SQLALCHEMY_DATABASE_URI` to the intended local development database with `ENV=development` (or explicitly direct a production migration), then rerun `db current`, `db heads`, inspect the planning columns, and apply the existing upgrade.

## Required changes

### 1. Repair the active local database first

From the repository's backend environment, target the same database used by the failing backend process.

Run and record:

```bash
cd backend
flask --app 'app:create_app' db current
flask --app 'app:create_app' db heads
```

Then apply existing migrations:

```bash
flask --app 'app:create_app' db upgrade
```

Run `db current` again and verify the active database is at the repository head that includes `f84c6e2a91b7`.

Verify the actual PostgreSQL schema contains:

```text
planned_bills.frequency
planned_bills.origin
planned_bills.account_id
```

Also verify the reconciliation did not drop or recreate planning data.

If `db upgrade` fails, stop and report the exact Alembic current revision, head revision, and failure. Do not generate a replacement migration unless repository topology proves `f84c6e2a91b7` is unreachable.

### 2. Make normal local direct-run migration-safe

File: `backend/run.py`

Before `app.run(...)`, bring the configured database to Alembic head using the existing Flask-Migrate integration.

Preferred shape:

```python
from pathlib import Path

from flask_migrate import upgrade

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _upgrade_database(app) -> None:
    with app.app_context():
        upgrade(directory=str(MIGRATIONS_DIR))


def main() -> None:
    app = create_app()
    _upgrade_database(app)
    app.run(host="0.0.0.0", static_files="static", port=5000, debug=True)
```

Exact import placement may follow repository formatting.

Requirements:

- Migration failure must abort local startup. Do not catch-and-log then continue.
- Do not call Alembic autogeneration.
- Do not call `db.create_all()` as a substitute.
- Do not alter production `wsgi.py`; deployment startup already owns migration application.
- Keep the helper small enough to unit test.
- Passing an absolute migrations directory is intentional so `python backend/run.py` behaves consistently regardless of the shell working directory.

If the current Flask-Migrate version exposes a materially different supported programmatic API, use that API, but preserve the same contract: upgrade to repository head before serving.

### 3. Add a regression test for startup ordering

Add:

`tests/test_run_entrypoint.py`

Test the direct-run helper/entrypoint without touching a real database.

At minimum assert:

- the migration upgrade is invoked before `app.run`;
- the configured migration directory resolves to `backend/migrations`;
- an upgrade exception prevents `app.run` from being called.

Prefer monkeypatch/mocks over spawning Flask.

### 4. Correct migration documentation

File: `README.md`

Replace the "After pulling schema changes" instructions with application of existing migrations only.

Target guidance:

```bash
cd backend
flask --app 'app:create_app' db upgrade
```

State explicitly:

- `db upgrade` applies revisions already committed to the repo;
- `db migrate` is for intentionally authoring a new schema revision after model changes, not for updating a pulled checkout;
- `python backend/run.py` now upgrades pending revisions before starting local development.

Update `AGENTS.md` only as needed so its local startup/migration guidance matches the implemented behavior.

## Do not rediscover

The root cause surface is already traced. Work only in:

- `backend/run.py`
- `README.md`
- `AGENTS.md` if needed for consistency
- `tests/test_run_entrypoint.py` (new)
- the active database migration state during validation

Reference-only files:

- `backend/app/models/planning_models.py`
- `backend/migrations/versions/f84c6e2a91b7_reconcile_legacy_planning_schema.py`
- `tests/test_planning_schema_migration.py`
- `backend/app/services/safe_to_spend.py`
- `backend/docker-entrypoint.sh`
- `render.yaml`

Do not perform a new Safe-to-Spend architecture pass.

## Non-goals

- Do not add another migration for `planned_bills.frequency`.
- Do not edit `PlannedBill` to remove `frequency`.
- Do not select only a subset of ORM columns to hide the mismatch.
- Do not catch `UndefinedColumn` and return zero upcoming bills.
- Do not rebuild planning tables.
- Do not reset, stamp, or manually edit `alembic_version` unless the normal Alembic upgrade is proven impossible and the exact reason is documented.
- Do not broaden into planning-feature redesign, Plaid reconnect work, or general migration cleanup.

## Implementation order

1. Confirm the failing local DB target and record `db current` / `db heads`.
2. Apply `flask --app 'app:create_app' db upgrade`.
3. Verify `planned_bills.frequency`, `origin`, and `account_id` exist.
4. Restart/retest Safe-to-Spend and confirm the UndefinedColumn failure is gone.
5. Harden `backend/run.py` to upgrade before serving.
6. Add `tests/test_run_entrypoint.py`.
7. Correct `README.md` migration guidance and synchronize `AGENTS.md` if necessary.
8. Run focused and completion validation.

## Focused validation

```bash
pytest -q tests/test_planning_schema_migration.py
pytest -q tests/test_run_entrypoint.py
pytest -q tests/test_safe_to_spend_service.py
pytest -q tests/test_safe_to_spend_integration.py
```

Then verify migration state:

```bash
cd backend
flask --app 'app:create_app' db current
flask --app 'app:create_app' db heads
```

Finally start the backend through the normal local path and verify the Safe-to-Spend dashboard request no longer emits:

```text
column planned_bills.frequency does not exist
```

## Acceptance criteria

- [ ] The active local database is upgraded through the current Alembic head containing `f84c6e2a91b7`.
- [ ] `planned_bills.frequency`, `planned_bills.origin`, and `planned_bills.account_id` exist in the active PostgreSQL database.
- [x] The existing reconciliation migration is used; no duplicate migration is created.
- [ ] Safe-to-Spend no longer fails with `UndefinedColumn` for `planned_bills.frequency`.
- [x] `python backend/run.py` applies pending Alembic migrations before starting the dev server in local environments and refuses migrations under `ENV=production`.
- [x] Migration failure aborts local startup rather than serving against a stale schema.
- [x] Direct-run migration behavior is covered by a focused unit test.
- [x] README no longer tells users to run `db migrate` merely to apply pulled schema changes.
- [x] Existing planning reconciliation tests still pass.
- [x] No Safe-to-Spend query weakening or planning-table rebuild is introduced.

## Completion report

Report:

1. pre-fix `db current` and `db heads`;
2. post-upgrade current revision;
3. confirmation of the three required `planned_bills` columns;
4. whether the failing Safe-to-Spend request now succeeds;
5. files changed;
6. exact local-start migration behavior implemented;
7. focused test results;
8. any deviation from this packet and why.
