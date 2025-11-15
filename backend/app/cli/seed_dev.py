"""Dev-only seeding helpers to quickly populate a fresh database."""

from datetime import date
from decimal import Decimal

import click
from app.extensions import db
from app.models import Account, Category, Institution, Transaction


@click.command("seed-dev")
def seed_dev() -> None:
    """Populate the database with a small set of demo data.

    This is safe to run multiple times; it only inserts records when the
    corresponding tables are empty.
    """
    if Transaction.query.first() or Account.query.first():
        click.echo("Seed data already present; skipping dev seed.")
        return

    click.echo("Seeding demo institution, account, category, and transaction data...")

    institution = Institution(
        name="Demo Bank",
        plaid_institution_id="ins_demo",
        url="https://example-bank.local",
    )
    db.session.add(institution)
    db.session.flush()

    account = Account(
        account_id="demo-checking",
        user_id="demo-user",
        name="Demo Checking",
        type="depository",
        subtype="checking",
        institution_name=institution.name,
        institution_db_id=institution.id,
        balance=Decimal("1234.56"),
    )
    db.session.add(account)

    category = Category(
        name="Groceries",
        group="expense",
        is_income=False,
    )
    db.session.add(category)
    db.session.flush()

    txn = Transaction(
        transaction_id="demo-txn-1",
        account_id=account.account_id,
        user_id="demo-user",
        date=date.today(),
        name="Demo Grocery Store",
        amount=Decimal("42.00"),
        pending=False,
        category_id=category.id,
    )
    db.session.add(txn)

    db.session.commit()
    click.echo("Dev seed complete. Demo data is ready.")
