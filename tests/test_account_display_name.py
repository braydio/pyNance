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

from app.extensions import db
from app.models import Account
from app.sql.account_logic import get_accounts_from_db


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


def test_get_accounts_from_db_includes_display_name(app_context):
    db.session.add(
        Account(
            account_id="acc-4",
            user_id="user-1",
            name="Joint",
            institution_name="SoFi",
            type="depository",
            subtype="savings",
            balance=Decimal("55.50"),
        )
    )
    db.session.commit()

    accounts = get_accounts_from_db()

    assert accounts[0]["name"] == "Joint"
    assert accounts[0]["display_name"] == "SoFi • Savings"
