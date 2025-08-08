#!/usr/bin/env python3
"""Utility to generate a fully populated demo database for pyNance."""

from __future__ import annotations

import importlib.util
import logging
import os
import random
import sys
import types
from datetime import date, datetime, timedelta
from pathlib import Path

from dateutil.relativedelta import relativedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Stub minimal app package and extensions to avoid loading the full Flask app
app_pkg = types.ModuleType("app")
extensions_mod = types.ModuleType("app.extensions")
db = SQLAlchemy()
extensions_mod.db = db
app_pkg.extensions = extensions_mod
app_pkg.__path__ = []
sys.modules["app"] = app_pkg
sys.modules["app.extensions"] = extensions_mod
config_mod = types.ModuleType("app.config")
config_mod.logger = logging.getLogger("generate_example_db")
app_pkg.config = config_mod
sys.modules["app.config"] = config_mod

models_path = BACKEND_DIR / "app" / "models.py"
spec = importlib.util.spec_from_file_location("app.models", models_path)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
sys.modules["app.models"] = models
Account = models.Account
Category = models.Category
Transaction = models.Transaction
Institution = models.Institution
PlaidAccount = models.PlaidAccount
PlaidItem = models.PlaidItem
PlaidWebhookLog = models.PlaidWebhookLog
TellerAccount = models.TellerAccount
AccountHistory = models.AccountHistory
RecurringTransaction = models.RecurringTransaction
TransactionRule = models.TransactionRule
PlaidTransactionMeta = models.PlaidTransactionMeta
FinancialGoal = models.FinancialGoal


def create_app(db_uri: str) -> Flask:
    """Create a minimal Flask app bound to the given database URI."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def seed_data() -> None:
    """Populate the database with demo records for all models."""
    example_bank = Institution(
        name="Example Bank",
        provider="manual",
        last_refreshed=datetime.now(),
    )
    db.session.add(example_bank)

    checking = Account(
        account_id="acc_checking",
        user_id="user_1",
        name="Checking Account",
        type="checking",
        subtype="checking",
        institution_name="Example Bank",
        institution=example_bank,
        status="active",
        is_hidden=False,
        balance=1000,
        link_type="manual",
    )
    credit = Account(
        account_id="acc_credit",
        user_id="user_1",
        name="Credit Card",
        type="credit",
        subtype="credit card",
        institution_name="Example Bank",
        institution=example_bank,
        status="active",
        is_hidden=False,
        balance=-500,
        link_type="manual",
    )

    plaid_account = PlaidAccount(
        account_id=checking.account_id,
        plaid_institution_id="ins_1",
        access_token="plaid-access-token",
        item_id="item_1",
        product="transactions",
        institution_id="inst_123",
        webhook="https://example.com/webhook",
        last_refreshed=datetime.now(),
        institution=example_bank,
        sync_cursor="cursor_1",
        is_active=True,
        last_error=None,
    )

    teller_account = TellerAccount(
        account_id=credit.account_id,
        access_token="teller-access-token",
        enrollment_id="enroll_1",
        teller_institution_id="teller_ins_1",
        provider="Teller",
        last_refreshed=datetime.now(),
        institution=example_bank,
    )

    plaid_item = PlaidItem(
        user_id="user_1",
        item_id="item_1",
        access_token="plaid-access-token",
        institution_name="Example Bank",
        product="transactions",
        last_refreshed=datetime.now(),
        is_active=True,
        last_error=None,
    )

    webhook_log = PlaidWebhookLog(
        event_type="TRANSACTIONS",
        webhook_type="TRANSACTIONS",
        webhook_code="DEFAULT_UPDATE",
        item_id="item_1",
        payload={"sample": "payload"},
        received_at=datetime.now(),
    )

    income_cat = Category(
        display_name="Income",
        primary_category="Income",
        detailed_category="Salary",
    )
    food_cat = Category(
        display_name="Food > Groceries",
        primary_category="Food",
        detailed_category="Groceries",
    )
    util_cat = Category(
        display_name="Utilities",
        primary_category="Utilities",
        detailed_category="",
    )
    travel_cat = Category(
        display_name="Travel",
        primary_category="Travel",
        detailed_category="",
    )

    db.session.add_all(
        [
            checking,
            credit,
            plaid_account,
            teller_account,
            plaid_item,
            webhook_log,
            income_cat,
            food_cat,
            util_cat,
            travel_cat,
        ]
    )
    db.session.commit()

    today = datetime.now().replace(day=1)
    transactions = []
    for i in range(12):
        month_start = today - relativedelta(months=i)
        salary_date = month_start + timedelta(days=1)
        transactions.append(
            Transaction(
                transaction_id=f"tx_income_{i}",
                account_id=checking.account_id,
                amount=2500,
                date=salary_date,
                description="Salary",
                category_id=income_cat.id,
                category="Income",
            )
        )
        for j in range(3):
            expense_date = month_start + timedelta(days=5 * (j + 1))
            transactions.append(
                Transaction(
                    transaction_id=f"tx_food_{i}_{j}",
                    account_id=checking.account_id,
                    amount=-random.uniform(20, 120),
                    date=expense_date,
                    description="Grocery",
                    category_id=food_cat.id,
                    category="Food",
                )
            )
        bill_date = month_start + timedelta(days=20)
        transactions.append(
            Transaction(
                transaction_id=f"tx_util_{i}",
                account_id=checking.account_id,
                amount=-random.uniform(50, 150),
                date=bill_date,
                description="Utility Bill",
                category_id=util_cat.id,
                category="Utilities",
            )
        )
        credit_date = month_start + timedelta(days=15)
        transactions.append(
            Transaction(
                transaction_id=f"tx_travel_{i}",
                account_id=credit.account_id,
                amount=-random.uniform(30, 200),
                date=credit_date,
                description="Travel Expense",
                category_id=travel_cat.id,
                category="Travel",
            )
        )
    db.session.add_all(transactions)
    db.session.commit()

    # Add Plaid metadata for the first grocery transaction
    sample_tx = transactions[1]
    meta = PlaidTransactionMeta(
        transaction=sample_tx,
        plaid_account_id=plaid_account.account_id,
        account_owner="John Doe",
        authorized_date=sample_tx.date.date(),
        authorized_datetime=sample_tx.date,
        category=["Food", "Groceries"],
        category_id="19013000",
        check_number="123",
        counterparties=[{"name": "Local Market"}],
        datetime=sample_tx.date,
        iso_currency_code="USD",
        location={"city": "Metropolis"},
        logo_url="https://example.com/logo.png",
        merchant_entity_id="merch_1",
        payment_channel="in_store",
        payment_meta={"reference_number": "ref123"},
        pending_transaction_id=None,
        transaction_code="purchase",
        transaction_type="special",
        unofficial_currency_code=None,
        website="https://market.example.com",
        pfc_confidence_level="HIGH",
        is_active=True,
    )
    db.session.add(meta)

    # Recurring transaction for utility bill
    util_tx = next(tx for tx in transactions if tx.transaction_id == "tx_util_0")
    recurring = RecurringTransaction(
        transaction=util_tx,
        account_id=util_tx.account_id,
        frequency="monthly",
        next_due_date=util_tx.date.date() + relativedelta(months=1),
        notes="Monthly utilities",
        next_instance_id="util_next_1",
    )
    db.session.add(recurring)

    # Transaction rule example
    rule = TransactionRule(
        user_id="user_1",
        match_criteria={"description": "Grocery"},
        action={"category": "Food"},
        is_active=True,
    )
    db.session.add(rule)

    # Financial goal
    goal = FinancialGoal(
        user_id="user_1",
        account_id=checking.account_id,
        name="Vacation Fund",
        target_amount=5000,
        due_date=date.today() + relativedelta(months=12),
        notes="Trip to Hawaii",
    )
    db.session.add(goal)

    # Explicit account history entry
    hist = AccountHistory(
        account_id=checking.account_id,
        user_id="user_1",
        date=datetime.now(),
        balance=checking.balance,
        is_hidden=False,
    )
    db.session.add(hist)
    db.session.commit()


def build_example_database(path: str) -> None:
    """Create the example database file and populate it."""
    uri = f"sqlite:///{path}"
    app = create_app(uri)
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        os.remove(db_path)
    with app.app_context():
        db.create_all()
        seed_data()


if __name__ == "__main__":
    base_path = (
        Path(__file__).resolve().parent.parent
        / "backend"
        / "app"
        / "data"
        / "example_database.db"
    )
    build_example_database(str(base_path))
    print(f"Example database written to {base_path}")
