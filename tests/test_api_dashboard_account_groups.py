"""Integration tests for the dashboard account group API endpoints."""

import os
import sys

from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from app.extensions import db  # noqa: E402
from app.models import Account  # noqa: E402
from app.routes.dashboard import dashboard as dashboard_bp  # noqa: E402


def create_app():
    """Create a Flask test app bound to the dashboard blueprint."""

    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    return app


def _insert_account(account_id: str):
    """Insert an account fixture for relationship testing."""

    acct = Account(
        account_id=account_id,
        name=f"Account {account_id}",
        balance=100.0,
        type="depository",
        institution_name="Bank",
    )
    db.session.add(acct)
    db.session.commit()


def test_account_group_flow():
    """Exercise the full lifecycle of account group operations."""

    app = create_app()
    with app.app_context():
        db.create_all()
    with app.test_client() as client, app.app_context():
        resp = client.get("/api/dashboard/account-groups")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["status"] == "success"
        default_id = payload["data"]["active_group_id"]

        create_resp = client.post(
            "/api/dashboard/account-groups",
            json={"name": "Savings"},
        )
        assert create_resp.status_code == 201
        created = create_resp.get_json()["data"]["group"]
        new_group_id = created["id"]
        assert created["name"] == "Savings"

        reorder = client.post(
            "/api/dashboard/account-groups/reorder",
            json={"group_ids": [new_group_id, default_id]},
        )
        assert reorder.status_code == 200

        activate = client.put(
            "/api/dashboard/account-groups/active",
            json={"group_id": default_id},
        )
        assert activate.status_code == 200
        assert activate.get_json()["data"]["active_group_id"] == default_id

        _insert_account("acc-1")
        add_resp = client.post(
            f"/api/dashboard/account-groups/{new_group_id}/accounts",
            json={"account_id": "acc-1"},
        )
        assert add_resp.status_code == 201
        accounts = add_resp.get_json()["data"]["group"]["accounts"]
        assert accounts[0]["account_id"] == "acc-1"

        remove_resp = client.delete(
            f"/api/dashboard/account-groups/{new_group_id}/accounts/acc-1"
        )
        assert remove_resp.status_code == 200
        assert remove_resp.get_json()["data"]["group"]["accounts"] == []

        delete_resp = client.delete(f"/api/dashboard/account-groups/{new_group_id}")
        assert delete_resp.status_code == 200
        data = delete_resp.get_json()["data"]
        assert len(data["groups"]) == 1

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_reorder_requires_ids_list():
    """Validate validation errors when reorder payloads are invalid."""

    app = create_app()
    with app.app_context():
        db.create_all()
    with app.test_client() as client, app.app_context():
        resp = client.post("/api/dashboard/account-groups/reorder", json={})
        assert resp.status_code == 400
        assert resp.get_json()["status"] == "error"

    with app.app_context():
        db.session.remove()
        db.drop_all()
