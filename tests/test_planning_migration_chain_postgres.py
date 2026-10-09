"""Exercise the historical Planning schema through the real Alembic graph."""

import os
from pathlib import Path
from uuid import uuid4

import app.config as app_config
import pytest
import sqlalchemy as sa
from app.extensions import db
from flask import Flask
from flask_migrate import Migrate, upgrade
from sqlalchemy import text

pytestmark = pytest.mark.integration

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "backend/migrations"


def _create_legacy_planning_schema(connection):
    # The baseline migration is model-generated and already contains the new
    # tables. Rebuild only this disposable test schema to match the archived
    # legacy revision that a real upgraded database inherited.
    connection.execute(text("DROP TABLE scenario_allocations, planned_bills, planning_scenarios CASCADE"))
    connection.execute(
        text(
            "CREATE TABLE planning_scenarios (id UUID PRIMARY KEY, name VARCHAR(120) NOT NULL, "
            "created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL)"
        )
    )
    connection.execute(
        text(
            "CREATE TABLE planned_bills (id UUID PRIMARY KEY, scenario_id UUID NOT NULL "
            "REFERENCES planning_scenarios(id) ON DELETE CASCADE, name VARCHAR(120) NOT NULL, "
            "amount_cents INTEGER NOT NULL, due_date DATE, category VARCHAR(80), predicted BOOLEAN NOT NULL, "
            "created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL, "
            "CONSTRAINT ck_planned_bills_amount_nonneg CHECK (amount_cents >= 0))"
        )
    )
    connection.execute(text("CREATE INDEX ix_planned_bills_scenario_id ON planned_bills(scenario_id)"))
    connection.execute(text("CREATE INDEX ix_planned_bills_scenario_due ON planned_bills(scenario_id, due_date)"))
    connection.execute(
        text(
            "CREATE TABLE scenario_allocations (id UUID PRIMARY KEY, scenario_id UUID NOT NULL "
            "REFERENCES planning_scenarios(id) ON DELETE CASCADE, target VARCHAR(160) NOT NULL, "
            "kind allocation_type NOT NULL, value INTEGER NOT NULL, created_at TIMESTAMP NOT NULL, "
            "updated_at TIMESTAMP NOT NULL, CONSTRAINT ck_alloc_value_semantics CHECK "
            "((kind = 'fixed' AND value >= 0) OR (kind = 'percent' AND value BETWEEN 0 AND 100)))"
        )
    )
    connection.execute(text("CREATE INDEX ix_allocations_scenario_kind ON scenario_allocations(scenario_id, kind)"))
    connection.execute(text("CREATE INDEX ix_scenario_allocations_scenario_id ON scenario_allocations(scenario_id)"))


def test_legacy_planning_schema_upgrades_through_alembic_head(monkeypatch):
    uri = os.environ.get("PYNANCE_TEST_DATABASE_URI")
    if not uri:
        pytest.skip("Set PYNANCE_TEST_DATABASE_URI to an isolated PostgreSQL instance")

    schema = "test_planning_chain_" + uuid4().hex
    root_engine = sa.create_engine(uri)
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"options": f"-c search_path={schema}"}},
    )
    db.init_app(app)
    Migrate(app, db, directory=str(MIGRATIONS_DIR))
    monkeypatch.setattr(app_config, "DB_SCHEMA", schema)

    try:
        with root_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))

        with app.app_context():
            upgrade(directory=str(MIGRATIONS_DIR), revision="55d16a2ff3e7")
            with db.engine.begin() as connection:
                # Reconstruct the schema at the tested revision: these tables
                # are introduced by later revisions but included in the current
                # model-generated baseline migration.
                tables = set(sa.inspect(connection).get_table_names(schema=schema))
                for table in ("llm_settings", "plaid_source_events"):
                    if table in tables:
                        connection.execute(text(f'DROP TABLE "{schema}"."{table}" CASCADE'))
                connection.execute(
                    text(f'DROP FUNCTION IF EXISTS "{schema}".reject_plaid_source_event_mutation() CASCADE')
                )
                constraints = {
                    item["name"] for item in sa.inspect(connection).get_unique_constraints("categories", schema=schema)
                }
                if "uq_category_composite" not in constraints:
                    connection.execute(
                        text(
                            f'ALTER TABLE "{schema}".categories ADD CONSTRAINT uq_category_composite '
                            "UNIQUE(primary_category, detailed_category)"
                        )
                    )
                _create_legacy_planning_schema(connection)
                connection.execute(
                    text(
                        "INSERT INTO planning_scenarios (id, name, created_at, updated_at) "
                        "VALUES ('00000000-0000-0000-0000-000000000001', 'Legacy scenario', now(), now())"
                    )
                )
                connection.execute(
                    text(
                        "INSERT INTO planned_bills (id, scenario_id, name, amount_cents, predicted, created_at, updated_at) "
                        "VALUES ('00000000-0000-0000-0000-000000000002', "
                        "'00000000-0000-0000-0000-000000000001', 'Legacy bill', 1200, false, now(), now())"
                    )
                )
                connection.execute(
                    text(
                        "INSERT INTO scenario_allocations (id, scenario_id, target, kind, value, created_at, updated_at) "
                        "VALUES ('00000000-0000-0000-0000-000000000003', "
                        "'00000000-0000-0000-0000-000000000001', 'Legacy target', 'fixed', 1200, now(), now())"
                    )
                )
                table_oids_before = connection.execute(
                    text(
                        "SELECT c.relname, c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                        "WHERE n.nspname=:schema AND c.relname IN "
                        "('planning_scenarios', 'planned_bills', 'scenario_allocations')"
                    ),
                    {"schema": schema},
                ).all()

            upgrade(directory=str(MIGRATIONS_DIR), revision="head")

            with db.engine.connect() as connection:
                version = connection.execute(text(f'SELECT version_num FROM "{schema}".alembic_version')).scalar_one()
                assert version == "f84c6e2a91b7"
                inspector = sa.inspect(connection)
                assert {"frequency", "origin", "account_id"}.issubset(
                    {column["name"] for column in inspector.get_columns("planned_bills", schema=schema)}
                )
                assert {"account_id", "planning_balance_cents", "currency_code"}.issubset(
                    {column["name"] for column in inspector.get_columns("planning_scenarios", schema=schema)}
                )
                assert "ix_planned_bills_account_id" in {
                    index["name"] for index in inspector.get_indexes("planned_bills", schema=schema)
                }
                assert "ix_planning_scenarios_account_id" in {
                    index["name"] for index in inspector.get_indexes("planning_scenarios", schema=schema)
                }
                table_oids_after = connection.execute(
                    text(
                        "SELECT c.relname, c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                        "WHERE n.nspname=:schema AND c.relname IN "
                        "('planning_scenarios', 'planned_bills', 'scenario_allocations')"
                    ),
                    {"schema": schema},
                ).all()
                assert dict(table_oids_after) == dict(table_oids_before)
                assert connection.execute(text(f'SELECT name FROM "{schema}".planning_scenarios')).scalar_one() == (
                    "Legacy scenario"
                )
                assert connection.execute(text(f'SELECT name FROM "{schema}".planned_bills')).scalar_one() == (
                    "Legacy bill"
                )
                assert connection.execute(text(f'SELECT target FROM "{schema}".scenario_allocations')).scalar_one() == (
                    "Legacy target"
                )
    finally:
        with root_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        root_engine.dispose()
