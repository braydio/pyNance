# PostgreSQL Migration Playbook

This guide documents how to migrate an existing SQLite deployment of pyNance to the new PostgreSQL-first stack.

## Prerequisites

- PostgreSQL 14+ accessible from your workstation or CI environment.
- `SQLALCHEMY_DATABASE_URI` configured for the target database (see `backend/example.env`).
- Legacy SQLite file (default `backend/app/data/dashboard_database.db`) available for export.

## 1. Snapshot The SQLite Database

```bash
cd backend
sqlite3 app/data/dashboard_database.db ".backup ./dashboard_database.backup"
sqlite3 app/data/dashboard_database.db ".dump" > ./sqlite_dump.sql
```

Keep the `.backup` file as a point-in-time snapshot in case the transfer needs to be re-run.

## 2. Prepare A Clean PostgreSQL Database

```bash
createdb pynance
psql -d postgres -c "CREATE USER pynance WITH PASSWORD 'change-me';"
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE pynance TO pynance;"
```

Update `SQLALCHEMY_DATABASE_URI` to `postgresql+psycopg://pynance:change-me@localhost:5432/pynance` (or your managed connection string).

## 3. Bootstrap Schema With Alembic

```bash
cd backend
flask db upgrade
```

The new baseline migration calls `metadata.create_all`, so this step lays down every table defined by the current SQLAlchemy models.

## 4. Load Data Into PostgreSQL

You can use `pgloader` for a direct copy or run the provided Python loader stub:

```bash
python scripts/sqlite_to_postgres.py --sqlite ./app/data/dashboard_database.db --dsn postgresql+psycopg://pynance:change-me@localhost:5432/pynance
```

The stub (to be expanded) iterates over core tables (`accounts`, `transactions`, `plaid_accounts`, etc.), adapts SQLite types to PostgreSQL, and bulk-inserts rows in dependency order.

## 5. Validate & Backfill

- Run `pytest -q` to ensure the API can talk to the new database.
- Spot-check counts: `SELECT count(*) FROM transactions;`, `SELECT count(*) FROM accounts;` and compare with the SQLite totals.
- Trigger a lightweight ingest (`flask sync-accounts`) to confirm upstream integrations still write cleanly.

## 6. Decommission SQLite Artifacts

Once PostgreSQL is verified:

- Remove the old SQLite file from deployed environments.
- Delete `SQLALCHEMY_DATABASE_URI` fallbacks or scripts that referenced the file.
- Update any scheduled jobs or backup routines to track the PostgreSQL instance instead.

## Troubleshooting

- **psycopg.errors.UniqueViolation**: Ensure dependent tables are loaded before child tables and use `ON CONFLICT` upserts only after the initial insert.
- **psycopg.errors.UndefinedTable**: Run `flask db upgrade` again; missing tables indicate the schema bootstrap did not complete.
- **Timezone differences**: Explicitly normalise `datetime` columns to UTC before insert if the original SQLite data stored naive timestamps.

Document the steps you took (especially any manual fixes) so we can automate them in a future migration script.
