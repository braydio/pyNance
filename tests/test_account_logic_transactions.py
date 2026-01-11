"""Integration-style tests for ``get_paginated_transactions`` running balances."""

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy import event

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
os.environ.setdefault("PLAID_CLIENT_ID", "sandbox-client")
os.environ.setdefault("PLAID_SECRET_KEY", "sandbox-secret")
os.environ.setdefault("CLIENT_NAME", "pyNance Test Suite")
os.environ.setdefault("BACKEND_PUBLIC_URL", "http://localhost")

from app.extensions import db
from app.models import Account, Tag, Transaction
from app.sql.account_logic import get_paginated_transactions


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
        yield
        db.session.remove()
        db.drop_all()


def _seed_transactions(
    amounts: list[Decimal] | None = None, tags: dict[str, list[str]] | None = None
):
    """Insert a single account with dated transactions in reverse chronological order.

    Args:
        amounts: Ordered list of transaction amounts starting from the most recent.
            Defaults to three positive amounts to keep the existing expectations intact.
        tags: Optional mapping of transaction_id to tag names for association.
    """

    account = Account(
        account_id="acc-1",
        user_id="user-1",
        name="Checking",
        type="depository",
        balance=Decimal("100.00"),
    )
    db.session.add(account)

    amounts = amounts or [
        Decimal("10.00"),
        Decimal("20.00"),
        Decimal("5.00"),
    ]
    base_date = datetime(2024, 3, 3, tzinfo=timezone.utc)
    timestamps = [base_date - timedelta(days=idx) for idx in range(len(amounts))]

    for idx, (ts, amount) in enumerate(zip(timestamps, amounts), start=1):
        txn_id = f"tx-{idx}"
        txn = Transaction(
            transaction_id=txn_id,
            account_id=account.account_id,
            user_id=account.user_id,
            amount=amount,
            date=ts,
            description=f"Txn {idx}",
        )
        if tags and txn_id in tags:
            for tag_name in tags[txn_id]:
                tag = Tag.query.filter_by(user_id=account.user_id, name=tag_name).first()
                if not tag:
                    tag = Tag(user_id=account.user_id, name=tag_name)
                    db.session.add(tag)
                txn.tags.append(tag)
        db.session.add(txn)

    db.session.commit()


def test_get_paginated_transactions_skips_running_balance_when_disabled(app_context):
    _seed_transactions()
    statements = []

    def capture_sql(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement.lower())

    event.listen(db.engine, "before_cursor_execute", capture_sql)
    try:
        rows, total, meta = get_paginated_transactions(
            1,
            2,
            user_id="user-1",
            include_running_balance=False,
        )
    finally:
        event.remove(db.engine, "before_cursor_execute", capture_sql)

    assert total == 3
    assert len(rows) == 2
    assert all(tx["running_balance"] is None for tx in rows)
    assert meta["page"] == 1
    assert any("limit" in stmt and "select" in stmt for stmt in statements)


def test_get_paginated_transactions_returns_running_balances_per_page(app_context):
    _seed_transactions()
    statements = []

    def capture_sql(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement.lower())

    event.listen(db.engine, "before_cursor_execute", capture_sql)
    try:
        page_one, total, meta = get_paginated_transactions(
            1,
            2,
            user_id="user-1",
            include_running_balance=True,
        )
        page_two, _, _ = get_paginated_transactions(
            2,
            2,
            user_id="user-1",
            include_running_balance=True,
        )
    finally:
        event.remove(db.engine, "before_cursor_execute", capture_sql)

    assert total == 3
    assert [tx["running_balance"] for tx in page_one] == [100.0, 90.0]
    assert page_two[0]["running_balance"] == pytest.approx(70.0)
    assert meta["page_size"] == 2
    assert any("limit" in stmt and "select" in stmt for stmt in statements)


def test_get_paginated_transactions_uses_amount_sign_over_type(app_context):
    _seed_transactions(
        [
            Decimal("-25.00"),
            Decimal("60.00"),
            Decimal("-15.00"),
        ]
    )

    rows, total, meta = get_paginated_transactions(
        1,
        5,
        user_id="user-1",
        include_running_balance=True,
    )

    assert total == 3
    assert [tx["running_balance"] for tx in rows] == [100.0, 125.0, 65.0]
    assert meta["page"] == 1


def test_get_paginated_transactions_serializes_tags_with_default(app_context):
    _seed_transactions(tags={"tx-1": ["groceries", "weekly"]})

    rows, total, meta = get_paginated_transactions(
        1,
        3,
        user_id="user-1",
        include_running_balance=False,
    )

    assert total == 3
    assert rows[0]["tags"] == ["groceries", "weekly"]
    assert rows[1]["tags"] == ["#untagged"]
    assert rows[2]["tags"] == ["#untagged"]
    assert meta["page"] == 1
