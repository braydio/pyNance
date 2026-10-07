"""Persistence behavior for Item-scoped Plaid reconnect status."""

import os

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

import pytest
from app.extensions import db
from app.models import Account, PlaidAccount, PlaidItem
from app.routes import plaid_webhook
from app.routes.accounts import accounts as accounts_blueprint
from app.sql.account_logic import (
    clear_plaid_item_reauth_required,
    mark_plaid_item_reauth_required,
    mark_refresh_success,
    serialized_plaid_item_connection_status,
)
from flask import Flask


@pytest.fixture()
def database():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        item = PlaidItem(user_id="owner", item_id="external-secret-item", access_token="secret", product="transactions")
        db.session.add(item)
        db.session.flush()
        accounts = [
            Account(account_id=f"account-{index}", user_id="owner", name=f"Account {index}", type="depository")
            for index in range(2)
        ]
        db.session.add_all(accounts)
        db.session.flush()
        links = [
            PlaidAccount(
                account_id=account.account_id, item_id=item.item_id, plaid_item_id=item.id, access_token="secret"
            )
            for account in accounts
        ]
        db.session.add_all(links)
        db.session.commit()
        yield app, item, links
        db.session.remove()
        db.drop_all()


def test_reauth_is_item_scoped_and_serializes_local_id_only(database):
    _app, item, _links = database
    mark_plaid_item_reauth_required(
        item_id=item.item_id,
        error={"code": "ITEM_LOGIN_REQUIRED", "message": "Please sign in again"},
        commit=True,
    )
    status = serialized_plaid_item_connection_status(item)
    assert status == {
        "provider": "plaid",
        "state": "reauth_required",
        "requires_reauth": True,
        "connection_id": item.id,
        "code": "ITEM_LOGIN_REQUIRED",
        "message": "Please sign in again",
        "updated_at": status["updated_at"],
    }
    assert item.item_id not in str(status)
    assert "secret" not in str(status)


def test_success_clears_only_reauth_and_preserves_other_item_error(database):
    _app, item, links = database
    item.last_error = '{"status":"reauth_required","code":"ITEM_LOGIN_REQUIRED"}'
    links[0].last_error = '{"status":"reauth_required","code":"ITEM_LOGIN_REQUIRED"}'
    links[1].last_error = '{"status":"error","code":"RATE_LIMIT_EXCEEDED"}'
    db.session.commit()
    clear_plaid_item_reauth_required(item_id=item.item_id, commit=True)
    assert item.last_error is None
    assert links[0].last_error is None
    assert "RATE_LIMIT_EXCEEDED" in links[1].last_error


def test_non_reauth_item_error_is_not_cleared(database):
    _app, item, links = database
    item.last_error = '{"status":"error","code":"INSTITUTION_DOWN"}'
    mark_refresh_success(links[0], commit=True)
    assert "INSTITUTION_DOWN" in item.last_error


def test_item_webhooks_set_and_clear_reauth_without_faking_refresh(database, monkeypatch):
    app, item, _links = database
    prior_refresh = item.last_refreshed
    monkeypatch.setattr(plaid_webhook, "_verify_plaid_signature", lambda _request: (True, None))
    app.register_blueprint(plaid_webhook.plaid_webhooks, url_prefix="/webhooks")
    with app.test_client() as client:
        response = client.post(
            "/webhooks/plaid",
            json={
                "webhook_type": "ITEM",
                "webhook_code": "ERROR",
                "item_id": item.item_id,
                "error": {
                    "error_code": "ITEM_LOGIN_REQUIRED",
                    "error_message": "Credentials changed",
                    "error_code_reason": "USER_ACTION_REQUIRED",
                },
            },
        )
        assert response.status_code == 200
        assert serialized_plaid_item_connection_status(item)["requires_reauth"] is True
        repaired = client.post(
            "/webhooks/plaid",
            json={"webhook_type": "ITEM", "webhook_code": "LOGIN_REPAIRED", "item_id": item.item_id},
        )
    assert repaired.status_code == 200
    assert serialized_plaid_item_connection_status(item)["state"] == "healthy"
    assert item.last_refreshed == prior_refresh


def test_account_endpoints_expose_item_connection_status_without_secrets(database):
    app, item, _links = database
    item.last_error = '{"status":"reauth_required","code":"ITEM_LOGIN_REQUIRED","message":"Sign in again"}'
    for account in Account.query.all():
        account.link_type = "plaid"
    db.session.commit()
    app.register_blueprint(accounts_blueprint, url_prefix="/api/accounts")
    with app.test_client() as client:
        accounts_response = client.get("/api/accounts/get_accounts")
        refresh_response = client.get("/api/accounts/refresh_status")
    statuses = [row["connection_status"] for row in accounts_response.get_json()["accounts"]]
    assert all(status["connection_id"] == item.id and status["requires_reauth"] for status in statuses)
    assert all("external-secret-item" not in str(status) and "secret" not in str(status) for status in statuses)
    assert all(row["connection_status"]["connection_id"] == item.id for row in refresh_response.get_json()["accounts"])
