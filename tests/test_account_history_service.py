import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")

if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
os.environ.setdefault("PLAID_CLIENT_ID", "sandbox-client")
os.environ.setdefault("PLAID_SECRET_KEY", "sandbox-secret")
os.environ.setdefault("CLIENT_NAME", "pyNance Test Suite")
os.environ.setdefault("BACKEND_PUBLIC_URL", "http://localhost")

import app.services.enhanced_account_history as enhanced_account_history  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Account, AccountHistory, Transaction  # noqa: E402
from app.services.account_history import compute_balance_history  # noqa: E402
from app.sql.account_logic import upsert_accounts  # noqa: E402


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


def test_compute_balance_history_reverse_mapping():
    txs = [
        {"date": date(2025, 8, 2), "amount": 25.0},
        {"date": date(2025, 8, 1), "amount": -50.0},
    ]
    start = date(2025, 8, 1)
    end = date(2025, 8, 3)
    result = compute_balance_history(Decimal("100.0"), txs, start, end)
    assert result == [
        {"date": "2025-08-01", "balance": 75.0},
        {"date": "2025-08-02", "balance": 100.0},
        {"date": "2025-08-03", "balance": 100.0},
    ]


def test_compute_balance_history_fills_gaps():
    txs = []
    start = date(2025, 1, 1)
    end = date(2025, 1, 3)
    result = compute_balance_history(Decimal("10.0"), txs, start, end)
    assert len(result) == 3
    assert result[0]["date"] == "2025-01-01"
    assert result[-1]["balance"] == 10.0


def test_upsert_accounts_normalizes_status(app_context):
    accounts = [
        {
            "account_id": "acct-1",
            "name": "Checking",
            "type": "depository",
            "balances": {"current": 100},
            "status": "ACTIVE",
        },
        {
            "account_id": "acct-2",
            "name": "Brokerage",
            "type": "investment",
            "balances": {"current": 50},
        },
        {
            "account_id": "acct-3",
            "name": "Credit",
            "type": "credit",
            "balances": {"current": -25},
            "status": "paused",
        },
    ]

    upsert_accounts("user-1", accounts, provider="PLAID")

    persisted = {
        account.account_id: account.status
        for account in Account.query.order_by(Account.account_id)
    }

    assert persisted == {
        "acct-1": "active",
        "acct-2": "active",
        "acct-3": "active",
    }


def test_cache_history_upserts_only_requested_window(app_context):
    """Cache updates should only modify rows inside the requested date window."""

    today = datetime.now(timezone.utc).date()
    start_365 = today - timedelta(days=364)

    account = Account(
        account_id="acct-history-window",
        user_id="user-window",
        name="Savings",
        type="depository",
        balance=Decimal("365.00"),
        link_type="manual",
    )
    db.session.add(account)

    original_rows = []
    original_balances = {}
    for offset in range(365):
        row_date = start_365 + timedelta(days=offset)
        balance_value = Decimal(str(1000 + offset)).quantize(Decimal("0.01"))
        history_row = AccountHistory(
            account_id=account.account_id,
            user_id=account.user_id,
            date=row_date,
            balance=balance_value,
            is_hidden=False,
        )
        original_rows.append(history_row)
        original_balances[row_date] = balance_value

    db.session.add_all(original_rows)
    db.session.commit()

    target_start = today - timedelta(days=29)
    replacement_history = []
    for offset in range(30):
        row_date = target_start + timedelta(days=offset)
        replacement_history.append(
            {
                "date": row_date.isoformat(),
                "balance": float(Decimal(str(5000 + offset)).quantize(Decimal("0.01"))),
            }
        )

    enhanced_account_history.cache_history(
        account.account_id,
        account.user_id,
        replacement_history,
    )

    all_rows = (
        AccountHistory.query.filter_by(account_id=account.account_id)
        .order_by(AccountHistory.date.asc())
        .all()
    )
    assert len(all_rows) == 365

    for row in all_rows:
        if target_start <= row.date <= today:
            expected_balance = Decimal(
                str(5000 + (row.date - target_start).days)
            ).quantize(Decimal("0.01"))
            assert row.balance == expected_balance
        else:
            assert row.balance == original_balances[row.date]


def test_get_or_compute_account_history_cache_matches_first_compute(app_context):
    """Ensure compute and cache-hit paths return identical balances for the same range."""

    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=2)

    account = Account(
        account_id="acct-history-1",
        user_id="user-1",
        name="Checking",
        type="depository",
        balance=Decimal("100.00"),
        link_type="manual",
    )
    db.session.add(account)

    db.session.add_all(
        [
            Transaction(
                transaction_id="tx-ext-1",
                account_id=account.account_id,
                user_id=account.user_id,
                amount=Decimal("10.00"),
                date=datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc),
                description="External deposit",
                provider="manual",
                is_internal=False,
            ),
            Transaction(
                transaction_id="tx-int-1",
                account_id=account.account_id,
                user_id=account.user_id,
                amount=Decimal("5.00"),
                date=datetime.combine(
                    start + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
                ),
                description="Internal transfer",
                provider="manual",
                is_internal=True,
            ),
        ]
    )
    db.session.commit()

    first_result = enhanced_account_history.get_or_compute_account_history(
        account.account_id,
        start_date=start,
        end_date=today,
        include_internal=False,
    )

    cached_rows = AccountHistory.query.filter_by(account_id=account.account_id).all()
    assert len(cached_rows) == 3

    second_result = enhanced_account_history.get_or_compute_account_history(
        account.account_id,
        start_date=start,
        end_date=today,
        include_internal=False,
    )

    assert first_result == second_result
