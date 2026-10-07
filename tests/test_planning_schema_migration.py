"""Tests for idempotent legacy planning-schema reconciliation."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "backend/migrations/versions/f84c6e2a91b7_reconcile_legacy_planning_schema.py"
)
spec = importlib.util.spec_from_file_location("planning_schema_migration", MIGRATION_PATH)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


def _run_upgrade(connection):
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        migration.upgrade()


def test_reconciliation_adds_only_missing_legacy_columns_and_indexes():
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(sa.text("CREATE TABLE planning_scenarios (id VARCHAR(36) PRIMARY KEY, name VARCHAR(120))"))
        connection.execute(
            sa.text(
                "CREATE TABLE planned_bills (id VARCHAR(36) PRIMARY KEY, scenario_id VARCHAR(36) NOT NULL, "
                "name VARCHAR(120) NOT NULL, amount_cents INTEGER NOT NULL, due_date DATE, "
                "category VARCHAR(80), predicted BOOLEAN NOT NULL, created_at DATETIME, updated_at DATETIME)"
            )
        )

        _run_upgrade(connection)
        _run_upgrade(connection)

        inspector = sa.inspect(connection)
        assert {
            "account_id",
            "planning_balance_cents",
            "currency_code",
        }.issubset({column["name"] for column in inspector.get_columns("planning_scenarios")})
        assert {"frequency", "origin", "account_id"}.issubset(
            {column["name"] for column in inspector.get_columns("planned_bills")}
        )
        assert "ix_planning_scenarios_account_id" in {
            index["name"] for index in inspector.get_indexes("planning_scenarios")
        }
        assert "ix_planned_bills_account_id" in {index["name"] for index in inspector.get_indexes("planned_bills")}


def test_reconciliation_is_noop_for_current_planning_schema():
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "CREATE TABLE planning_scenarios (id VARCHAR(36) PRIMARY KEY, name VARCHAR(120), "
                "account_id VARCHAR(128), planning_balance_cents INTEGER NOT NULL DEFAULT 0, "
                "currency_code VARCHAR(3) NOT NULL DEFAULT 'USD', created_at DATETIME, updated_at DATETIME)"
            )
        )
        connection.execute(
            sa.text(
                "CREATE TABLE planned_bills (id VARCHAR(36) PRIMARY KEY, scenario_id VARCHAR(36) NOT NULL, "
                "name VARCHAR(120) NOT NULL, amount_cents INTEGER NOT NULL, due_date DATE, "
                "frequency VARCHAR(20) NOT NULL DEFAULT 'monthly', category VARCHAR(80), "
                "origin VARCHAR(20) NOT NULL DEFAULT 'manual', account_id VARCHAR(128), "
                "predicted BOOLEAN NOT NULL, created_at DATETIME, updated_at DATETIME)"
            )
        )
        connection.execute(sa.text("CREATE INDEX ix_planning_scenarios_account_id ON planning_scenarios(account_id)"))
        connection.execute(sa.text("CREATE INDEX ix_planned_bills_account_id ON planned_bills(account_id)"))

        _run_upgrade(connection)

        inspector = sa.inspect(connection)
        assert len(inspector.get_columns("planning_scenarios")) == 7
        assert len(inspector.get_columns("planned_bills")) == 12
