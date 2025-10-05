"""Integration tests covering database cascade semantics and mixin timestamps."""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy import text

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    Account,
    AccountGroup,
    AccountGroupMembership,
    AccountHistory,
    Category,
    FinancialGoal,
    Institution,
    InvestmentHolding,
    InvestmentTransaction,
    PlaidAccount,
    PlaidTransactionMeta,
    PlanningScenario,
    PlannedBill,
    RecurringTransaction,
    ScenarioAllocation,
    Security,
    TellerAccount,
    Transaction,
)


@pytest.fixture()
def app_context():
    """Provide an application context backed by an in-memory SQLite database."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.execute(text("PRAGMA foreign_keys = ON"))
        yield
        db.session.remove()
        db.drop_all()


def test_institution_delete_cascades_account_tree(app_context):
    """Deleting an institution removes dependent accounts and related records."""

    institution = Institution(name="Cascade Bank", provider="Plaid")
    db.session.add(institution)
    db.session.commit()

    account = Account(
        account_id="acct-1",
        name="Primary",
        type="depository",
        institution_name="Cascade",
        institution_db_id=institution.id,
    )
    db.session.add(account)
    db.session.flush()

    db.session.add_all(
        [
            AccountHistory(
                account_id=account.account_id,
                user_id="user-1",
                date=datetime.now(timezone.utc),
                balance=Decimal("10.00"),
            ),
            FinancialGoal(
                user_id="user-1",
                account_id=account.account_id,
                name="Emergency Fund",
                target_amount=Decimal("1000.00"),
                due_date=date(2025, 1, 1),
            ),
            PlaidAccount(
                account_id=account.account_id,
                access_token="token",
                item_id="item-1",
                product="transactions",
            ),
            TellerAccount(
                account_id=account.account_id,
                access_token="token",
            ),
        ]
    )

    category = Category(primary_category="Bills", detailed_category="Utilities")
    db.session.add(category)
    db.session.flush()

    transaction = Transaction(
        transaction_id="txn-1",
        account_id=account.account_id,
        amount=Decimal("25.00"),
        date=datetime.now(timezone.utc),
    )
    transaction.category_id = category.id
    db.session.add(transaction)
    db.session.flush()

    db.session.add_all(
        [
            PlaidTransactionMeta(
                transaction_id=transaction.transaction_id,
                plaid_account_id=account.account_id,
            ),
            RecurringTransaction(
                transaction_id=transaction.transaction_id,
                account_id=account.account_id,
                frequency="monthly",
                next_due_date=date(2025, 1, 1),
            ),
        ]
    )

    security = Security(security_id="sec-1", name="Fund")
    db.session.add(security)
    db.session.flush()

    db.session.add_all(
        [
            InvestmentHolding(
                account_id=account.account_id,
                security_id=security.security_id,
                quantity=Decimal("1"),
            ),
            InvestmentTransaction(
                investment_transaction_id="inv-1",
                account_id=account.account_id,
                security_id=security.security_id,
                amount=Decimal("5.00"),
            ),
        ]
    )

    group = AccountGroup(user_id="user-1", name="Group")
    db.session.add(group)
    db.session.flush()

    db.session.add(
        AccountGroupMembership(group_id=group.id, account_id=account.account_id)
    )
    db.session.commit()

    db.session.delete(institution)
    db.session.commit()

    assert db.session.query(Account).count() == 0
    assert db.session.query(AccountHistory).count() == 0
    assert db.session.query(FinancialGoal).count() == 0
    assert db.session.query(Transaction).count() == 0
    assert db.session.query(RecurringTransaction).count() == 0
    assert db.session.query(PlaidTransactionMeta).count() == 0
    assert db.session.query(PlaidAccount).count() == 0
    assert db.session.query(TellerAccount).count() == 0
    assert db.session.query(InvestmentHolding).count() == 0
    assert db.session.query(InvestmentTransaction).count() == 0
    assert db.session.query(AccountGroupMembership).count() == 0
    assert db.session.query(AccountGroup).count() == 1


def test_category_delete_retains_transactions(app_context):
    """Deleting a category preserves dependent rows but clears their foreign keys."""

    category = Category(primary_category="Parent", detailed_category="Parent")
    child = Category(
        primary_category="Child",
        detailed_category="Child",
        parent=category,
    )
    db.session.add_all([category, child])

    account = Account(account_id="acct-2", name="Secondary", type="other")
    db.session.add(account)
    db.session.flush()

    txn = Transaction(
        transaction_id="txn-2",
        account_id=account.account_id,
        amount=Decimal("15.00"),
        date=datetime.now(timezone.utc),
    )
    txn.category_id = category.id
    db.session.add(txn)
    db.session.commit()

    db.session.delete(category)
    db.session.commit()

    assert db.session.get(Category, child.id).parent_id is None
    remaining_txn = db.session.query(Transaction).filter_by(transaction_id="txn-2").one()
    assert remaining_txn.category_id is None


def test_security_delete_sets_transaction_security_null(app_context):
    """Security deletion cascades holdings while retaining transactions with NULL FKs."""

    security = Security(security_id="sec-2", name="Stock")
    account = Account(account_id="acct-3", name="Brokerage", type="brokerage")
    db.session.add_all([security, account])
    db.session.flush()

    holding = InvestmentHolding(
        account_id=account.account_id,
        security_id=security.security_id,
        quantity=Decimal("2"),
    )
    txn = InvestmentTransaction(
        investment_transaction_id="inv-2",
        account_id=account.account_id,
        security_id=security.security_id,
        amount=Decimal("20.00"),
    )
    db.session.add_all([holding, txn])
    db.session.commit()

    db.session.delete(security)
    db.session.commit()

    assert db.session.query(InvestmentHolding).count() == 0
    remaining_txn = (
        db.session.query(InvestmentTransaction)
        .filter_by(investment_transaction_id="inv-2")
        .one()
    )
    assert remaining_txn.security_id is None


def test_planning_models_use_timestamp_mixin(app_context):
    """Planning models should automatically populate created/updated timestamps."""

    scenario = PlanningScenario(name="Baseline")
    scenario.bills.append(
        PlannedBill(name="Rent", amount_cents=120000, due_date=None, predicted=False)
    )
    scenario.allocations.append(
        ScenarioAllocation(target="Savings", kind="percent", value=20)
    )

    db.session.add(scenario)
    db.session.commit()

    assert scenario.created_at is not None
    assert scenario.updated_at is not None
    bill = scenario.bills[0]
    alloc = scenario.allocations[0]
    assert bill.created_at is not None
    assert bill.updated_at is not None
    assert alloc.created_at is not None
    assert alloc.updated_at is not None

    original_updated = scenario.updated_at
    scenario.name = "Updated Baseline"
    db.session.commit()
    db.session.refresh(scenario)
    assert scenario.updated_at >= original_updated
