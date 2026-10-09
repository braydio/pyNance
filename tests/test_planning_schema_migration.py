"""Tests for idempotent legacy planning-schema reconciliation."""

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "backend/migrations/versions/f84c6e2a91b7_reconcile_legacy_planning_schema.py"
)
spec = importlib.util.spec_from_file_location("planning_schema_migration", MIGRATION_PATH)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)

PERSISTENCE_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "backend/migrations/versions/6b0f2c9d1a34_add_planning_persistence_tables.py"
)
spec = importlib.util.spec_from_file_location("planning_persistence_migration", PERSISTENCE_MIGRATION_PATH)
persistence_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(persistence_migration)


def _run_upgrade(connection):
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        migration.upgrade()


def _run_persistence_upgrade(connection):
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        persistence_migration.upgrade()


def _create_legacy_planning_tables(connection):
    connection.execute(
        sa.text(
            "CREATE TABLE planning_scenarios (id VARCHAR(36) PRIMARY KEY, name VARCHAR(120) NOT NULL, "
            "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
        )
    )
    connection.execute(
        sa.text(
            "CREATE TABLE planned_bills (id VARCHAR(36) PRIMARY KEY, scenario_id VARCHAR(36) NOT NULL "
            "REFERENCES planning_scenarios(id) ON DELETE CASCADE, name VARCHAR(120) NOT NULL, "
            "amount_cents INTEGER NOT NULL, due_date DATE, category VARCHAR(80), predicted BOOLEAN NOT NULL, "
            "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, "
            "CONSTRAINT ck_planned_bills_amount_nonneg CHECK(amount_cents >= 0))"
        )
    )
    connection.execute(sa.text("CREATE INDEX ix_planned_bills_scenario_id ON planned_bills(scenario_id)"))
    connection.execute(sa.text("CREATE INDEX ix_planned_bills_scenario_due ON planned_bills(scenario_id, due_date)"))
    connection.execute(
        sa.text(
            "CREATE TABLE scenario_allocations (id VARCHAR(36) PRIMARY KEY, scenario_id VARCHAR(36) NOT NULL "
            "REFERENCES planning_scenarios(id) ON DELETE CASCADE, target VARCHAR(160) NOT NULL, "
            "kind VARCHAR(7) NOT NULL, value INTEGER NOT NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
        )
    )
    connection.execute(sa.text("CREATE INDEX ix_allocations_scenario_kind ON scenario_allocations(scenario_id, kind)"))
    connection.execute(sa.text("CREATE INDEX ix_scenario_allocations_scenario_id ON scenario_allocations(scenario_id)"))


def test_persistence_migration_reuses_and_preserves_legacy_tables():
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_legacy_planning_tables(connection)
        connection.execute(
            sa.text(
                "INSERT INTO planning_scenarios VALUES "
                "('scenario-1', 'Legacy', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO planned_bills VALUES "
                "('bill-1', 'scenario-1', 'Rent', 1000, NULL, 'Housing', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO scenario_allocations VALUES "
                "('allocation-1', 'scenario-1', 'Rent', 'fixed', 1000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )

        _run_persistence_upgrade(connection)
        _run_persistence_upgrade(connection)

        inspector = sa.inspect(connection)
        assert set(inspector.get_table_names()) >= {
            "planning_scenarios",
            "planned_bills",
            "scenario_allocations",
        }
        assert (
            connection.execute(sa.text("SELECT name FROM planning_scenarios WHERE id='scenario-1'")).scalar_one()
            == "Legacy"
        )
        assert connection.execute(sa.text("SELECT name FROM planned_bills WHERE id='bill-1'")).scalar_one() == "Rent"
        assert (
            connection.execute(sa.text("SELECT target FROM scenario_allocations WHERE id='allocation-1'")).scalar_one()
            == "Rent"
        )
        assert "ix_planned_bills_scenario_id" in {index["name"] for index in inspector.get_indexes("planned_bills")}

        context = MigrationContext.configure(connection)
        with Operations.context(context):
            persistence_migration.downgrade()
        assert {
            "planning_scenarios",
            "planned_bills",
            "scenario_allocations",
        }.issubset(sa.inspect(connection).get_table_names())
        assert connection.execute(sa.text("SELECT count(*) FROM planning_scenarios")).scalar_one() == 1
        assert connection.execute(sa.text("SELECT count(*) FROM planned_bills")).scalar_one() == 1
        assert connection.execute(sa.text("SELECT count(*) FROM scenario_allocations")).scalar_one() == 1


def test_persistence_migration_rejects_incompatible_existing_table():
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(sa.text("CREATE TABLE planning_scenarios (id VARCHAR(36) PRIMARY KEY)"))
        with pytest.raises(RuntimeError, match="missing required legacy columns: created_at, name, updated_at"):
            _run_persistence_upgrade(connection)


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
