"""Tests for canonical account display naming and serialization."""

import os
import sys
from decimal import Decimal

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.extensions import db  # noqa: E402
from app.models import Account  # noqa: E402
from app.sql.account_logic import get_accounts_from_db  # noqa: E402


@pytest.fixture()
def app_context():
    """Provide an in-memory application context for account model tests."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def test_display_name_prefers_institution_subtype_and_mask(app_context):
    account = Account(
        account_id="acc-1",
        user_id="user-1",
        name="Everyday Checking",
        institution_name="Chase",
        type="depository",
        subtype="checking",
        balance=Decimal("100.00"),
    )

    assert account.display_name == "Chase • Checking"
    assert account.format_display_name(mask="1234") == "Chase • Checking • •••• 1234"


def test_display_name_falls_back_when_metadata_missing(app_context):
    account = Account(
        account_id="acc-2",
        user_id="user-1",
        name="Primary Account",
        institution_name=None,
        type=None,
        subtype=None,
        balance=Decimal("0.00"),
    )

    assert account.display_name == "Primary Account"


def test_display_name_uses_type_when_subtype_is_missing(app_context):
    account = Account(
        account_id="acc-3",
        user_id="user-1",
        name="Backup",
        institution_name="Capital One",
        type="credit",
        subtype=None,
        balance=Decimal("10.00"),
    )

    assert account.display_name == "Capital One • Credit"


def test_display_name_uses_last4_when_mask_not_provided(app_context):
    account = Account(
        account_id="acc-3b",
        user_id="user-1",
        name="Travel Card",
        institution_name="AmEx",
        type="credit",
        subtype="credit card",
        balance=Decimal("10.00"),
    )

    assert account.format_display_name(last4="9876") == "AmEx • Credit Card • •••• 9876"


def test_display_name_handles_missing_name_and_metadata(app_context):
    account = Account(
        account_id="acc-3c",
        user_id="user-1",
        name="",
        institution_name=None,
        type=None,
        subtype=None,
        balance=Decimal("0.00"),
    )

    assert account.display_name == "Unnamed Account"


def test_get_accounts_from_db_includes_display_name_and_investment_semantics(
    app_context,
):
    db.session.add_all(
        [
            Account(
                account_id="acc-4",
                user_id="user-1",
                name="Joint",
                institution_name="SoFi",
                type="depository",
                subtype="savings",
                balance=Decimal("55.50"),
            ),
            Account(
                account_id="acc-5",
                user_id="user-1",
                name="Brokerage",
                institution_name="Fidelity",
                type="brokerage",
                subtype="brokerage",
                balance=Decimal("1055.50"),
                is_investment=True,
                investment_has_holdings=True,
                investment_has_transactions=True,
                product_provenance="product_scope",
            ),
        ]
    )
    db.session.commit()

    accounts = get_accounts_from_db()

    by_id = {account["account_id"]: account for account in accounts}

    assert by_id["acc-4"]["name"] == "Joint"
    assert by_id["acc-4"]["display_name"] == "SoFi • Savings"
    assert by_id["acc-4"]["account_type"] == "depository"
    assert by_id["acc-4"]["is_investment"] is False

    assert by_id["acc-5"]["type"] == "investment"
    assert by_id["acc-5"]["account_type"] == "investment"
    assert by_id["acc-5"]["is_investment"] is True
    assert by_id["acc-5"]["investment_has_holdings"] is True
    assert by_id["acc-5"]["investment_has_transactions"] is True
