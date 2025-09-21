"""Tests for the account group service helper functions."""

import os
import sys

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from app.extensions import db  # noqa: E402
from app.models import Account  # noqa: E402
from app.services import account_groups  # noqa: E402


@pytest.fixture
def app_context():
    """Provide an application context with an in-memory database."""

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


def _create_account(account_id: str, name: str = "Checking", balance: float = 0.0):
    """Insert an account used when populating groups.

    Args:
        account_id: External identifier for the account.
        name: Display name to persist.
        balance: Starting balance for the account.

    Returns:
        Account: Persisted account model instance.
    """

    account = Account(
        account_id=account_id,
        name=name,
        balance=balance,
        type="depository",
        institution_name="Bank",
    )
    db.session.add(account)
    db.session.commit()
    return account


def test_list_account_groups_creates_default(app_context):
    """Ensure listing initializes a default group when none exist."""

    data = account_groups.list_account_groups(user_id="user-1")
    assert data["groups"][0]["name"] == "Group"
    assert data["active_group_id"] == data["groups"][0]["id"]


def test_create_group_sets_active_and_position(app_context):
    """Verify created groups are positioned and activated."""

    account_groups.list_account_groups(user_id="user-1")
    created = account_groups.create_account_group(
        name="Savings", user_id="user-1", group_id="custom-id"
    )
    assert created["group"]["id"] == "custom-id"
    assert created["group"]["name"] == "Savings"
    assert created["active_group_id"] == "custom-id"

    listing = account_groups.list_account_groups(user_id="user-1")
    positions = [group["position"] for group in listing["groups"]]
    assert positions == sorted(positions)


def test_add_account_to_group_enforces_limit(app_context):
    """Check the service enforces the per-group account limit."""

    listing = account_groups.list_account_groups(user_id="user-1")
    group_id = listing["groups"][0]["id"]
    for idx in range(account_groups.MAX_ACCOUNTS_PER_GROUP):
        _create_account(f"acc-{idx}", name=f"Account {idx}")
        result = account_groups.add_account_to_group(
            group_id, f"acc-{idx}", user_id="user-1"
        )
        assert len(result["group"]["accounts"]) == idx + 1

    _create_account("acc-overflow", name="Overflow")
    with pytest.raises(ValueError):
        account_groups.add_account_to_group(group_id, "acc-overflow", user_id="user-1")


def test_remove_group_promotes_fallback(app_context):
    """Ensure active groups fail over to the remaining record."""

    first = account_groups.list_account_groups(user_id="user-1")
    original_group_id = first["groups"][0]["id"]
    created = account_groups.create_account_group(name="Secondary", user_id="user-1")
    new_group_id = created["group"]["id"]

    account_groups.set_active_group(original_group_id, user_id="user-1")
    payload = account_groups.delete_account_group(new_group_id, user_id="user-1")
    assert payload["active_group_id"] == original_group_id
    assert len(payload["groups"]) == 1
