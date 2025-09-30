"""Break circular accounts ↔ institutions cycle

Revision ID: b1c2d3e4f5a6
Revises: 85a7cc1f25b6
Create Date: 2025-07-20 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "85a7cc1f25b6"
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Create tables without FKs (if not already present)
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("institutions"):
        op.create_table(
            "institutions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("provider", sa.String(length=64), nullable=False),
            sa.Column("last_refreshed", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    if not insp.has_table("accounts"):
        op.create_table(
            "accounts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("account_id", sa.String(length=64), nullable=False, unique=True),
            sa.Column("user_id", sa.String(length=64), nullable=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("type", sa.String(length=64), nullable=True),
            sa.Column("subtype", sa.String(length=64), nullable=True),
            sa.Column("institution_name", sa.String(length=128), nullable=True),
            sa.Column("institution_db_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=64), nullable=True),
            sa.Column("is_hidden", sa.Boolean(), nullable=True),
            sa.Column("balance", sa.Float(), nullable=True),
            sa.Column("link_type", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    account_fks = {fk["name"] for fk in insp.get_foreign_keys("accounts")}
    if "fk_accounts_institution_db_id_institutions" not in account_fks:
        op.create_foreign_key(
            "fk_accounts_institution_db_id_institutions",
            "accounts",
            "institutions",
            ["institution_db_id"],
            ["id"],
        )


def downgrade():
    # Drop FK first
    op.drop_constraint(
        "fk_accounts_institution_db_id_institutions", "accounts", type_="foreignkey"
    )
    # Drop tables
    op.drop_table("accounts")
    op.drop_table("institutions")
