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


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        allocation_type.create(bind, checkfirst=True)

    uuid_type = postgresql.UUID(as_uuid=True)
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
    op.create_index(op.f("ix_planning_scenarios_account_id"), "planning_scenarios", ["account_id"], unique=False)

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
    op.create_index(op.f("ix_planned_bills_account_id"), "planned_bills", ["account_id"], unique=False)
    op.create_index(op.f("ix_planned_bills_scenario_id"), "planned_bills", ["scenario_id"], unique=False)
    op.create_index("ix_planned_bills_scenario_due", "planned_bills", ["scenario_id", "due_date"], unique=False)

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
    op.create_index("ix_allocations_scenario_kind", "scenario_allocations", ["scenario_id", "kind"], unique=False)
    op.create_index(
        op.f("ix_scenario_allocations_scenario_id"),
        "scenario_allocations",
        ["scenario_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_scenario_allocations_scenario_id"), table_name="scenario_allocations")
    op.drop_index("ix_allocations_scenario_kind", table_name="scenario_allocations")
    op.drop_table("scenario_allocations")

    op.drop_index("ix_planned_bills_scenario_due", table_name="planned_bills")
    op.drop_index(op.f("ix_planned_bills_scenario_id"), table_name="planned_bills")
    op.drop_index(op.f("ix_planned_bills_account_id"), table_name="planned_bills")
    op.drop_table("planned_bills")

    op.drop_index(op.f("ix_planning_scenarios_account_id"), table_name="planning_scenarios")
    op.drop_table("planning_scenarios")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        allocation_type.drop(bind, checkfirst=True)
