"""add planning persistence tables

Revision ID: 6b0f2c9d1a34
Revises: 2c4d6e8f9a10
Create Date: 2026-04-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "6b0f2c9d1a34"
down_revision = "2c4d6e8f9a10"
branch_labels = None
depends_on = None


allocation_type = postgresql.ENUM("fixed", "percent", name="allocation_type", create_type=False)


def _table_names(bind):
    return set(sa.inspect(bind).get_table_names())


def _validate_existing_table(bind, table_name, required_columns):
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    missing = set(required_columns) - columns
    if missing:
        raise RuntimeError(
            f"Existing {table_name} table is missing required legacy columns: {', '.join(sorted(missing))}"
        )
    primary_key = inspector.get_pk_constraint(table_name).get("constrained_columns") or []
    if primary_key != ["id"]:
        raise RuntimeError(f"Existing {table_name} table must have id as its primary key")


def _ensure_index(bind, index_name, table_name, columns):
    inspector = sa.inspect(bind)
    existing = {index["name"]: index for index in inspector.get_indexes(table_name)}
    if index_name in existing:
        actual_columns = existing[index_name]["column_names"]
        if actual_columns != columns:
            raise RuntimeError(
                f"Existing index {index_name} on {table_name} has columns {actual_columns}, expected {columns}"
            )
        return
    available_columns = {column["name"] for column in inspector.get_columns(table_name)}
    if not set(columns).issubset(available_columns):
        return
    op.create_index(index_name, table_name, columns, unique=False)


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        allocation_type.create(bind, checkfirst=True)

    uuid_type = postgresql.UUID(as_uuid=True)
    tables = _table_names(bind)
    if "planning_scenarios" in tables:
        _validate_existing_table(bind, "planning_scenarios", {"id", "name", "created_at", "updated_at"})
    else:
        op.create_table(
            "planning_scenarios",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("account_id", sa.String(length=128), nullable=True),
            sa.Column("planning_balance_cents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="USD"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "planned_bills" in tables:
        _validate_existing_table(
            bind,
            "planned_bills",
            {
                "id",
                "scenario_id",
                "name",
                "amount_cents",
                "due_date",
                "category",
                "predicted",
                "created_at",
                "updated_at",
            },
        )
    else:
        op.create_table(
            "planned_bills",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("scenario_id", uuid_type, nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("amount_cents", sa.Integer(), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("frequency", sa.String(length=20), nullable=False, server_default="monthly"),
            sa.Column("category", sa.String(length=80), nullable=True),
            sa.Column("origin", sa.String(length=20), nullable=False, server_default="manual"),
            sa.Column("account_id", sa.String(length=128), nullable=True),
            sa.Column("predicted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint("amount_cents >= 0", name="ck_planned_bills_amount_nonneg"),
            sa.ForeignKeyConstraint(["scenario_id"], ["planning_scenarios.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if "scenario_allocations" in tables:
        _validate_existing_table(
            bind,
            "scenario_allocations",
            {"id", "scenario_id", "target", "kind", "value", "created_at", "updated_at"},
        )
    else:
        op.create_table(
            "scenario_allocations",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("scenario_id", uuid_type, nullable=False),
            sa.Column("target", sa.String(length=160), nullable=False),
            sa.Column("kind", allocation_type, nullable=False),
            sa.Column("value", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.CheckConstraint(
                "(kind = 'fixed' AND value >= 0) OR (kind = 'percent' AND value BETWEEN 0 AND 100)",
                name="ck_alloc_value_semantics",
            ),
            sa.ForeignKeyConstraint(["scenario_id"], ["planning_scenarios.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    _ensure_index(bind, op.f("ix_planned_bills_scenario_id"), "planned_bills", ["scenario_id"])
    _ensure_index(bind, "ix_planned_bills_scenario_due", "planned_bills", ["scenario_id", "due_date"])
    _ensure_index(bind, "ix_allocations_scenario_kind", "scenario_allocations", ["scenario_id", "kind"])
    _ensure_index(bind, op.f("ix_scenario_allocations_scenario_id"), "scenario_allocations", ["scenario_id"])


def downgrade():
    # This revision can inherit these tables from the archived Planning
    # migration, so their origin cannot be determined safely during downgrade.
    # Keep the tables, indexes, and enum intact to avoid deleting user data.
    return
