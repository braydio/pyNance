"""reconcile legacy planning schema

Revision ID: f84c6e2a91b7
Revises: e6a9c2f4b8d1
Create Date: 2026-10-07

"""

import sqlalchemy as sa
from alembic import op

revision = "f84c6e2a91b7"
down_revision = "e6a9c2f4b8d1"
branch_labels = None
depends_on = None


def _column_names(inspector, table_name):
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector, table_name):
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    required = {"planning_scenarios", "planned_bills"}
    missing_tables = required - tables
    if missing_tables:
        raise RuntimeError(
            "Planning schema reconciliation requires existing tables: " + ", ".join(sorted(missing_tables))
        )

    scenario_columns = _column_names(inspector, "planning_scenarios")
    if "account_id" not in scenario_columns:
        op.add_column("planning_scenarios", sa.Column("account_id", sa.String(length=128), nullable=True))
    if "planning_balance_cents" not in scenario_columns:
        op.add_column(
            "planning_scenarios",
            sa.Column("planning_balance_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        )
    if "currency_code" not in scenario_columns:
        op.add_column(
            "planning_scenarios",
            sa.Column("currency_code", sa.String(length=3), nullable=False, server_default=sa.text("'USD'")),
        )

    bill_columns = _column_names(inspector, "planned_bills")
    if "frequency" not in bill_columns:
        op.add_column(
            "planned_bills",
            sa.Column("frequency", sa.String(length=20), nullable=False, server_default=sa.text("'monthly'")),
        )
    if "origin" not in bill_columns:
        op.add_column(
            "planned_bills",
            sa.Column("origin", sa.String(length=20), nullable=False, server_default=sa.text("'manual'")),
        )
    if "account_id" not in bill_columns:
        op.add_column("planned_bills", sa.Column("account_id", sa.String(length=128), nullable=True))

    inspector = sa.inspect(bind)
    if "ix_planning_scenarios_account_id" not in _index_names(inspector, "planning_scenarios"):
        op.create_index("ix_planning_scenarios_account_id", "planning_scenarios", ["account_id"], unique=False)
    if "ix_planned_bills_account_id" not in _index_names(inspector, "planned_bills"):
        op.create_index("ix_planned_bills_account_id", "planned_bills", ["account_id"], unique=False)


def downgrade():
    # Existing installations may have had these columns before this revision.
    # Their original state cannot be inferred safely, so downgrade is a no-op.
    pass
