"""Tests for the tag metrics charts endpoint."""

import os
import sys
from datetime import datetime, timezone
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

from app.extensions import db
from app.models import Account, Tag, Transaction
from app.routes.charts import charts


def _seed_tag_metrics():
    account = Account(
        account_id="acc-1",
        user_id="user-1",
        name="Checking",
        type="depository",
        balance=Decimal("100.00"),
        is_hidden=False,
    )
    db.session.add(account)

    tag_coffee = Tag(user_id=account.user_id, name="#coffee")
    tag_groceries = Tag(user_id=account.user_id, name="#groceries")
    db.session.add_all([tag_coffee, tag_groceries])

    tx1 = Transaction(
        transaction_id="tx-1",
        account_id=account.account_id,
        user_id=account.user_id,
        amount=Decimal("-12.50"),
        date=datetime(2024, 1, 5, tzinfo=timezone.utc),
        description="Coffee",
    )
    tx1.tags.append(tag_coffee)
    db.session.add(tx1)

    tx2 = Transaction(
        transaction_id="tx-2",
        account_id=account.account_id,
        user_id=account.user_id,
        amount=Decimal("-30.00"),
        date=datetime(2024, 1, 6, tzinfo=timezone.utc),
        description="Groceries",
    )
    tx2.tags.append(tag_groceries)
    db.session.add(tx2)

    tx3 = Transaction(
        transaction_id="tx-3",
        account_id=account.account_id,
        user_id=account.user_id,
        amount=Decimal("-7.00"),
        date=datetime(2024, 1, 7, tzinfo=timezone.utc),
        description="Untagged",
    )
    db.session.add(tx3)

    db.session.commit()


@pytest.fixture()
def client():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    app.register_blueprint(charts, url_prefix="/api/charts")
    with app.app_context():
        db.create_all()
        _seed_tag_metrics()
        with app.test_client() as test_client:
            yield test_client
        db.session.remove()
        db.drop_all()


def test_tag_metrics_returns_totals_and_counts(client):
    resp = client.get("/api/charts/tag_metrics?start_date=2024-01-01&end_date=2024-01-31")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] == "success"

    metrics = {item["tag"]: item for item in payload["data"]}
    assert metrics["#coffee"]["total"] == 12.5
    assert metrics["#coffee"]["count"] == 1
    assert metrics["#groceries"]["total"] == 30.0
    assert metrics["#groceries"]["count"] == 1
    assert metrics["#untagged"]["total"] == 7.0
    assert metrics["#untagged"]["count"] == 1
