"""Remove Teller integration artifacts from the schema."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3d2c4a1b6e7"
down_revision = "9d3f4c21a7b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop Teller tables and enum variants now that the integration is removed."""

    bind = op.get_bind()

    # Drop Teller-specific data before tightening enum constraints.
    op.execute(
        sa.text("UPDATE accounts SET link_type = 'manual' WHERE link_type = 'teller'")
    )
    op.execute(
        sa.text("UPDATE transactions SET provider = 'manual' WHERE provider = 'teller'")
    )

    # Remove Teller from the link_type enum used by accounts.
    op.execute(sa.text("ALTER TYPE link_type RENAME TO link_type_old"))
    link_type_old = sa.Enum(
        "manual", "plaid", "teller", name="link_type_old", create_type=False
    )
    link_type_new = sa.Enum("manual", "plaid", name="link_type")
    link_type_new.create(bind, checkfirst=False)
    op.alter_column(
        "accounts",
        "link_type",
        existing_type=link_type_old,
        type_=link_type_new,
        postgresql_using="link_type::text::link_type",
    )
    op.execute(sa.text("DROP TYPE link_type_old"))

    # Remove Teller from the provider_type enum used by transactions.
    op.execute(sa.text("ALTER TYPE provider_type RENAME TO provider_type_old"))
    provider_type_old = sa.Enum(
        "manual", "plaid", "teller", name="provider_type_old", create_type=False
    )
    provider_type_new = sa.Enum("manual", "plaid", name="provider_type")
    provider_type_new.create(bind, checkfirst=False)
    op.alter_column(
        "transactions",
        "provider",
        existing_type=provider_type_old,
        type_=provider_type_new,
        postgresql_using="provider::text::provider_type",
    )
    op.execute(sa.text("DROP TYPE provider_type_old"))

    # Finally drop the Teller account table entirely.
    op.drop_table("teller_accounts")


def downgrade() -> None:
    """Recreate Teller schema components if the integration needs to return."""

    bind = op.get_bind()

    # Recreate Teller table structure.
    op.create_table(
        "teller_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.String(length=64),
            sa.ForeignKey("accounts.account_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("access_token", sa.String(length=256), nullable=False),
        sa.Column("enrollment_id", sa.String(length=128), nullable=True),
        sa.Column("teller_institution_id", sa.String(length=128), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("last_refreshed", sa.DateTime(), nullable=True),
        sa.Column(
            "institution_db_id",
            sa.Integer(),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # Restore Teller enum variants for accounts.
    op.execute(sa.text("ALTER TYPE link_type RENAME TO link_type_old"))
    link_type_old = sa.Enum("manual", "plaid", name="link_type_old", create_type=False)
    link_type_new = sa.Enum("manual", "plaid", "teller", name="link_type")
    link_type_new.create(bind, checkfirst=False)
    op.alter_column(
        "accounts",
        "link_type",
        existing_type=link_type_old,
        type_=link_type_new,
        postgresql_using="link_type::text::link_type",
    )
    op.execute(sa.text("DROP TYPE link_type_old"))

    # Restore Teller enum variants for transactions.
    op.execute(sa.text("ALTER TYPE provider_type RENAME TO provider_type_old"))
    provider_type_old = sa.Enum(
        "manual", "plaid", name="provider_type_old", create_type=False
    )
    provider_type_new = sa.Enum("manual", "plaid", "teller", name="provider_type")
    provider_type_new.create(bind, checkfirst=False)
    op.alter_column(
        "transactions",
        "provider",
        existing_type=provider_type_old,
        type_=provider_type_new,
        postgresql_using="provider::text::provider_type",
    )
    op.execute(sa.text("DROP TYPE provider_type_old"))
