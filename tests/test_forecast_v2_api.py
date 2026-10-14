"""POST /api/forecast/compute: V1 stays the default, V2 is explicit, scoped and validated."""

import os
import sys

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from app.extensions import db
from app.routes.forecast import forecast
from flask import Flask
from forecast_v2_world import START, seed_world


@pytest.fixture()
def client():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False, TESTING=True)
    db.init_app(app)
    app.register_blueprint(forecast, url_prefix="/api/forecast")
    with app.app_context():
        db.create_all()
        seed_world()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def post(client, **body):
    return client.post("/api/forecast/compute", json={"user_id": "alice", "start_date": START.isoformat(), **body})


def test_default_and_explicit_v1_return_the_legacy_shape(client):
    legacy = post(client, horizon_days=10)
    explicit = post(client, horizon_days=10, model_version="v1")
    for response in (legacy, explicit):
        assert response.status_code == 200
        body = response.get_json()
        assert set(body) == {"timeline", "summary", "cashflows", "adjustments", "series", "metadata"}
        assert len(body["timeline"]) == 10
        assert "model_version" not in body and "liquidity" not in body
    assert legacy.get_json()["timeline"] == explicit.get_json()["timeline"]


def test_unknown_model_version_is_a_400(client):
    response = post(client, model_version="v3")
    assert response.status_code == 400 and "model_version" in response.get_json()["error"]


def test_v2_returns_additive_contract_with_v1_keys(client):
    response = post(client, model_version="v2", horizon_days=14)
    assert response.status_code == 200
    body = response.get_json()
    assert {"timeline", "summary", "cashflows", "adjustments", "series", "metadata"} <= set(body)
    assert {"model_version", "liquidity", "uncertainty", "drivers", "data_quality", "scenarios", "net_worth"} <= set(
        body
    )
    assert body["model_version"] == "v2" and body["liquidity"]["starting_cash"] == 5000.0
    assert len(body["timeline"]) == 14 and body["uncertainty"]["available"] is False


def test_v2_includes_bands_only_when_requested(client):
    body = post(
        client, model_version="v2", horizon_days=14, simulation={"enabled": True, "count": 100, "seed": 5}
    ).get_json()
    assert body["uncertainty"]["available"] is True
    assert all({"p10", "p50", "p90"} <= set(row) for row in body["timeline"])


def test_v2_rejects_foreign_accounts_with_403_and_leaks_nothing(client):
    response = post(client, model_version="v2", included_account_ids=["bob-chk"])
    assert response.status_code == 403
    assert "777" not in response.get_data(as_text=True) and "Bob" not in response.get_data(as_text=True)
    other_user = client.post(
        "/api/forecast/compute",
        json={
            "user_id": "bob",
            "start_date": START.isoformat(),
            "model_version": "v2",
            "included_account_ids": ["chk"],
        },
    )
    assert other_user.status_code == 403


def test_v2_validation_errors_are_400s(client):
    assert post(client, model_version="v2", horizon_days=999).status_code == 400
    assert post(client, model_version="v2", simulation={"enabled": True, "count": 5000}).status_code == 400
    assert post(client, model_version="v2", scenarios=[{"id": "x", "changes": {"nope": 1}}]).status_code == 400
    assert client.post("/api/forecast/compute", json={"model_version": "v2"}).status_code == 400


def test_v2_scenarios_are_request_local_and_not_persisted(client):
    scenario = [{"id": "cut", "label": "Cut", "changes": {"residual_spending_multiplier": 0.5}}]
    first = post(client, model_version="v2", horizon_days=20, scenarios=scenario).get_json()
    again = post(client, model_version="v2", horizon_days=20).get_json()
    assert first["scenarios"][1]["delta_vs_baseline"]["ending_cash"] > 0
    assert again["scenarios"] == []
    assert first["timeline"] == again["timeline"]  # baseline unaffected by the scenario call
