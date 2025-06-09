#!/usr/bin/env python3
"""Utility to generate a sample database for the pyNance dashboard."""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from dateutil.relativedelta import relativedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import sys
import types
import importlib.util

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

models_path = BACKEND_DIR / "app" / "models.py"
spec = importlib.util.spec_from_file_location("app.models", models_path)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
sys.modules["app.models"] = models
Account = models.Account
Category = models.Category
Transaction = models.Transaction

ah_path = BACKEND_DIR / "app" / "helpers" / "account_history_helper.py"
ah_spec = importlib.util.spec_from_file_location(
    "app.helpers.account_history_helper", ah_path
)
ah_mod = importlib.util.module_from_spec(ah_spec)
ah_spec.loader.exec_module(ah_mod)
sys.modules["app.helpers.account_history_helper"] = ah_mod
update_account_history = ah_mod.update_account_history


def create_app(db_uri: str) -> Flask:
    """Create a minimal Flask app bound to the given database URI."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def seed_data() -> None:
    """Populate the database with 12 months of mock records."""
    checking = Account(
        account_id="acc_checking",
        name="Checking Account",
        type="checking",
        subtype="checking",
        institution_name="Example Bank",
        balance=1000,
        link_type="manual",
    )
    credit = Account(
        account_id="acc_credit",
        name="Credit Card",
        type="credit",
        subtype="credit card",
        institution_name="Example Bank",
        balance=-500,
        link_type="manual",
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

    db.session.add_all([checking, credit, income_cat, food_cat, util_cat, travel_cat])
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
    db.session.bulk_save_objects(transactions)
    db.session.commit()

    # Generate account history for forecasting features
    update_account_history()


def build_example_database(path: str) -> None:
    """Create the example database file and populate it."""
    uri = f"sqlite:///{path}"
    app = create_app(uri)
    if os.path.exists(path):
        os.remove(path)
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
