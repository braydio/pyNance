"""Align foreign key ON DELETE rules with application expectations."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8f2b541c2d5a"
down_revision = "4b9af1d3db6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.drop_constraint("accounts_institution_db_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "accounts_institution_db_id_fkey",
            "institutions",
            ["institution_db_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("account_history") as batch_op:
        batch_op.drop_constraint("account_history_account_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "account_history_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("financial_goals") as batch_op:
        batch_op.drop_constraint("financial_goals_account_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "financial_goals_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("plaid_accounts") as batch_op:
        batch_op.drop_constraint("plaid_accounts_account_id_fkey", type_="foreignkey")
        batch_op.drop_constraint(
            "plaid_accounts_institution_db_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "plaid_accounts_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "plaid_accounts_institution_db_id_fkey",
            "institutions",
            ["institution_db_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("teller_accounts") as batch_op:
        batch_op.drop_constraint("teller_accounts_account_id_fkey", type_="foreignkey")
        batch_op.drop_constraint(
            "teller_accounts_institution_db_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "teller_accounts_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "teller_accounts_institution_db_id_fkey",
            "institutions",
            ["institution_db_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("categories") as batch_op:
        batch_op.drop_constraint("categories_parent_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "categories_parent_id_fkey",
            "categories",
            ["parent_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint("transactions_account_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("transactions_category_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "transactions_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "transactions_category_id_fkey",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("recurring_transactions") as batch_op:
        batch_op.drop_constraint(
            "recurring_transactions_transaction_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "recurring_transactions_account_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "recurring_transactions_transaction_id_fkey",
            "transactions",
            ["transaction_id"],
            ["transaction_id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "recurring_transactions_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("plaid_transaction_meta") as batch_op:
        batch_op.drop_constraint(
            "plaid_transaction_meta_transaction_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "plaid_transaction_meta_plaid_account_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "plaid_transaction_meta_transaction_id_fkey",
            "transactions",
            ["transaction_id"],
            ["transaction_id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "plaid_transaction_meta_plaid_account_id_fkey",
            "plaid_accounts",
            ["plaid_account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("investment_holdings") as batch_op:
        batch_op.drop_constraint(
            "investment_holdings_account_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "investment_holdings_security_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "investment_holdings_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "investment_holdings_security_id_fkey",
            "securities",
            ["security_id"],
            ["security_id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("investment_transactions") as batch_op:
        batch_op.drop_constraint(
            "investment_transactions_account_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "investment_transactions_security_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "investment_transactions_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "investment_transactions_security_id_fkey",
            "securities",
            ["security_id"],
            ["security_id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("investment_transactions") as batch_op:
        batch_op.drop_constraint(
            "investment_transactions_security_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "investment_transactions_account_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "investment_transactions_security_id_fkey",
            "securities",
            ["security_id"],
            ["security_id"],
        )
        batch_op.create_foreign_key(
            "investment_transactions_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
        )

    with op.batch_alter_table("investment_holdings") as batch_op:
        batch_op.drop_constraint(
            "investment_holdings_security_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "investment_holdings_account_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "investment_holdings_security_id_fkey",
            "securities",
            ["security_id"],
            ["security_id"],
        )
        batch_op.create_foreign_key(
            "investment_holdings_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
        )

    with op.batch_alter_table("plaid_transaction_meta") as batch_op:
        batch_op.drop_constraint(
            "plaid_transaction_meta_plaid_account_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "plaid_transaction_meta_transaction_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "plaid_transaction_meta_plaid_account_id_fkey",
            "plaid_accounts",
            ["plaid_account_id"],
            ["account_id"],
        )
        batch_op.create_foreign_key(
            "plaid_transaction_meta_transaction_id_fkey",
            "transactions",
            ["transaction_id"],
            ["transaction_id"],
        )

    with op.batch_alter_table("recurring_transactions") as batch_op:
        batch_op.drop_constraint(
            "recurring_transactions_account_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "recurring_transactions_transaction_id_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "recurring_transactions_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
        )
        batch_op.create_foreign_key(
            "recurring_transactions_transaction_id_fkey",
            "transactions",
            ["transaction_id"],
            ["transaction_id"],
        )

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint("transactions_category_id_fkey", type_="foreignkey")
        batch_op.drop_constraint("transactions_account_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "transactions_category_id_fkey",
            "categories",
            ["category_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "transactions_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
        )

    with op.batch_alter_table("categories") as batch_op:
        batch_op.drop_constraint("categories_parent_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "categories_parent_id_fkey",
            "categories",
            ["parent_id"],
            ["id"],
        )

    with op.batch_alter_table("teller_accounts") as batch_op:
        batch_op.drop_constraint(
            "teller_accounts_institution_db_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint("teller_accounts_account_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "teller_accounts_institution_db_id_fkey",
            "institutions",
            ["institution_db_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "teller_accounts_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
        )

    with op.batch_alter_table("plaid_accounts") as batch_op:
        batch_op.drop_constraint(
            "plaid_accounts_institution_db_id_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint("plaid_accounts_account_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "plaid_accounts_institution_db_id_fkey",
            "institutions",
            ["institution_db_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "plaid_accounts_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
        )

    with op.batch_alter_table("financial_goals") as batch_op:
        batch_op.drop_constraint("financial_goals_account_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "financial_goals_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
        )

    with op.batch_alter_table("account_history") as batch_op:
        batch_op.drop_constraint("account_history_account_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "account_history_account_id_fkey",
            "accounts",
            ["account_id"],
            ["account_id"],
        )

    with op.batch_alter_table("accounts") as batch_op:
        batch_op.drop_constraint("accounts_institution_db_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "accounts_institution_db_id_fkey",
            "institutions",
            ["institution_db_id"],
            ["id"],
        )
