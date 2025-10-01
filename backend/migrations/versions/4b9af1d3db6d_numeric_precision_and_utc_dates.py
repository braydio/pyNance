"""Switch monetary floats to numeric values and ensure UTC-aware timestamps."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4b9af1d3db6d"
down_revision = "cc9e65c88885"
branch_labels = None
depends_on = None

NUMERIC = sa.Numeric(18, 2)


def _alter_numeric(
    table: str, column: str, nullable: bool, default_zero: bool = False
) -> None:
    """Convert ``table.column`` from float to ``NUMERIC(18, 2)``."""

    if not nullable:
        op.execute(f"UPDATE {table} SET {column} = 0 WHERE {column} IS NULL")

    op.alter_column(
        table,
        column,
        type_=NUMERIC,
        existing_type=sa.Float(),
        nullable=nullable,
        server_default=sa.text("0") if default_zero else None,
        postgresql_using=f"ROUND({column}::numeric, 2)",
    )


def upgrade() -> None:
    _alter_numeric("transactions", "amount", nullable=False, default_zero=True)
    op.alter_column(
        "transactions",
        "date",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        nullable=False,
        postgresql_using="({column} AT TIME ZONE 'UTC')".format(column="date"),
    )

    _alter_numeric("accounts", "balance", nullable=False, default_zero=True)
    _alter_numeric("account_history", "balance", nullable=False, default_zero=True)
    _alter_numeric("financial_goals", "target_amount", nullable=False)

    _alter_numeric("securities", "institution_price", nullable=True)
    _alter_numeric("investment_holdings", "quantity", nullable=True)
    _alter_numeric("investment_holdings", "cost_basis", nullable=True)
    _alter_numeric("investment_holdings", "institution_value", nullable=True)

    _alter_numeric("investment_transactions", "amount", nullable=True)
    _alter_numeric("investment_transactions", "price", nullable=True)
    _alter_numeric("investment_transactions", "quantity", nullable=True)
    _alter_numeric("investment_transactions", "fees", nullable=True)


def downgrade() -> None:
    op.alter_column(
        "transactions",
        "date",
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="({column} AT TIME ZONE 'UTC')".format(column="date"),
    )
    op.alter_column(
        "transactions",
        "amount",
        type_=sa.Float(),
        existing_type=NUMERIC,
        nullable=False,
        server_default=sa.text("0"),
        postgresql_using="{column}::double precision".format(column="amount"),
    )

    op.alter_column(
        "accounts",
        "balance",
        type_=sa.Float(),
        existing_type=NUMERIC,
        nullable=False,
        server_default=sa.text("0"),
        postgresql_using="{column}::double precision".format(column="balance"),
    )
    op.alter_column(
        "account_history",
        "balance",
        type_=sa.Float(),
        existing_type=NUMERIC,
        nullable=False,
        server_default=sa.text("0"),
        postgresql_using="{column}::double precision".format(column="balance"),
    )
    op.alter_column(
        "financial_goals",
        "target_amount",
        type_=sa.Float(),
        existing_type=NUMERIC,
        nullable=False,
        postgresql_using="{column}::double precision".format(column="target_amount"),
    )

    for table, column in [
        ("securities", "institution_price"),
        ("investment_holdings", "quantity"),
        ("investment_holdings", "cost_basis"),
        ("investment_holdings", "institution_value"),
        ("investment_transactions", "amount"),
        ("investment_transactions", "price"),
        ("investment_transactions", "quantity"),
        ("investment_transactions", "fees"),
    ]:
        op.alter_column(
            table,
            column,
            type_=sa.Float(),
            existing_type=NUMERIC,
            nullable=True,
            postgresql_using="{column}::double precision".format(column=column),
        )
