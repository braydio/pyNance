"""Recurring review API: owner scope, durable decisions, atomic scans, stable response shape."""

import os

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from datetime import date
from decimal import Decimal

import pytest
from app.extensions import db
from app.models import Account, RecurringStream, RecurringStreamEvidence, Transaction
from app.routes import recurring as recurring_routes
from app.routes.recurring import recurring
from app.services import recurring_repository as repo
from flask import Flask

AS_OF = date(2026, 10, 17)


@pytest.fixture()
def app(monkeypatch):
    flask_app = Flask(__name__)
    flask_app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(flask_app)
    flask_app.register_blueprint(recurring, url_prefix="/api/recurring")
    monkeypatch.setenv(repo.OWNER_ENV, "alice")

    class FrozenDate(date):
        @classmethod
        def today(cls):
            return AS_OF

    monkeypatch.setattr(recurring_routes, "date", FrozenDate)
    monkeypatch.setattr(repo, "date", FrozenDate)
    with flask_app.app_context():
        db.create_all()
        for account_id, user, name in (
            ("chk", "alice", "Checking"),
            ("sav", "alice", "Savings"),
            ("bob", "bob", "Bob"),
        ):
            db.session.add(
                Account(account_id=account_id, user_id=user, name=name, type="depository", subtype="checking")
            )
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def add_rent(account="chk", user="alice", months=(7, 8, 9)):
    for m in months:
        db.session.add(
            Transaction(
                transaction_id=f"secret-{account}-{m}",
                user_id=user,
                account_id=account,
                date=date(2026, m, 21),
                amount=Decimal("700.00"),
                provider="plaid",
                description=f"RENT PAYMENT {m:02d}",
            )
        )
    db.session.commit()


def manual(client, **overrides):
    body = {
        "account_id": "chk",
        "display_name": "Duke Energy",
        "amount_cash_delta": "-142.37",
        "amount_mode": "variable",
        "cadence": "monthly",
        "anchor_date": "2026-11-03",
    }
    body.update(overrides)
    return client.post("/api/recurring/streams", json=body)


def post(client, path, **body):
    return client.post(f"/api/recurring/{path}", json=body)


# ----------------------------------------------------------------------------- manual plans


def test_manual_plan_needs_only_account_name_amount_and_date(client):
    response = manual(client)
    assert response.status_code == 201
    stream = response.get_json()["stream"]
    assert stream["status"] == "confirmed" and stream["source"] == "manual"
    assert stream["amount_cash_delta"] == "-142.37" and stream["next_due_date"] == "2026-11-03"
    assert stream["amount_range"] == {"min": "-142.37", "max": "-142.37"}
    assert stream["reason_codes"] == ["manual_plan"] and stream["evidence_count"] == 0
    assert Transaction.query.count() == 0


def test_manual_plan_validation_and_scope(client):
    assert manual(client, account_id="bob").status_code == 404
    assert manual(client, account_id="nope").status_code == 404
    assert manual(client, cadence="sometimes").status_code == 400
    assert manual(client, amount_cash_delta="lots").status_code == 400
    assert manual(client, display_name="").status_code == 400
    assert RecurringStream.query.count() == 0


def test_every_endpoint_fails_closed_without_a_trusted_owner(app, monkeypatch):
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    client = app.test_client()
    calls = [
        client.get("/api/recurring/streams"),
        client.get("/api/recurring/candidates"),
        client.post("/api/recurring/scan", json={}),
        client.post("/api/recurring/streams", json={}),
        client.patch("/api/recurring/streams/x", json={}),
        client.post("/api/recurring/streams/x/decision", json={"decision": "ignored"}),
        client.delete("/api/recurring/streams/x"),
    ]
    assert [c.status_code for c in calls] == [503] * 7
    assert {c.get_json()["code"] for c in calls} == {"owner_not_configured"}


# ----------------------------------------------------------------------------- listing


def test_streams_are_paginated_filtered_and_owner_scoped(client):
    for i in range(45):
        manual(client, display_name=f"Plan {i:02d}", anchor_date=f"2026-11-{(i % 28) + 1:02d}")
    repo.create_manual(
        "bob",
        account_id="bob",
        display_name="Bob plan",
        amount_cash_delta="-5",
        cadence="monthly",
        anchor_date="2026-11-01",
    )
    first = client.get("/api/recurring/streams?page_size=1").get_json()  # clamped up to the 20-row minimum
    assert first["page_size"] == 20 and first["total"] == 45 and len(first["streams"]) == 20
    last = client.get("/api/recurring/streams?page_size=20&page=3").get_json()
    assert len(last["streams"]) == 5
    assert client.get("/api/recurring/streams?page_size=5000").get_json()["page_size"] == 100
    assert "Bob plan" not in str(first)

    repo.update_stream("alice", RecurringStream.query.filter_by(user_id="alice").first().id, status="ignored")
    assert client.get("/api/recurring/streams?status=ignored").get_json()["total"] == 1
    assert client.get("/api/recurring/streams?status=confirmed,ignored").get_json()["total"] == 45
    assert client.get("/api/recurring/streams?status=bogus").status_code == 400
    assert client.get("/api/recurring/streams?account_id=bob").status_code == 404
    assert client.get("/api/recurring/streams?account_id=sav").get_json()["total"] == 0


# ----------------------------------------------------------------------------- scan + candidates


def test_scan_is_read_only_by_default_then_saves_one_atomic_batch(client):
    add_rent()
    dry = post(client, "scan")
    body = dry.get_json()
    assert dry.status_code == 200 and body["dry_run"] is True
    assert RecurringStream.query.count() == 0 and RecurringStreamEvidence.query.count() == 0
    candidate = body["candidates"][0]
    assert candidate["status"] == "candidate" and candidate["stream_id"] is None
    assert candidate["cadence"] == "monthly" and candidate["amount_cash_delta"] == "-700.00"
    assert candidate["next_due_date"] == "2026-10-21" and candidate["ready"] is True
    assert body["summary"]["history_incomplete"] is True

    saved = post(client, "scan", dry_run=False).get_json()
    assert saved["summary"]["created"] == 1
    assert RecurringStream.query.count() == 1
    again = post(client, "scan", dry_run=False).get_json()
    assert (again["summary"]["created"], again["summary"]["updated"]) == (0, 1)
    assert RecurringStream.query.count() == 1


def test_scan_rejects_foreign_accounts_before_any_work(client):
    add_rent(account="bob", user="bob")
    add_rent()
    response = post(client, "scan", account_ids=["chk", "bob"], dry_run=False)
    assert response.status_code == 404
    assert RecurringStream.query.count() == 0
    assert post(client, "scan", account_ids="chk").status_code == 400
    assert post(client, "scan", lookback_days="many").status_code == 400
    narrowed = post(client, "scan", account_ids=["sav"]).get_json()
    assert narrowed["candidates"] == []


def test_a_failed_batch_save_rolls_everything_back(client, monkeypatch):
    add_rent()
    calls = {"n": 0}
    real = repo.upsert_detected_candidate

    def flaky(owner_id, candidate, *, commit=True):
        calls["n"] += 1
        real(owner_id, candidate, commit=commit)
        raise RuntimeError("disk full")  # fails after the first write, before the final commit

    monkeypatch.setattr(repo, "upsert_detected_candidate", flaky)
    response = post(client, "scan", dry_run=False)
    assert response.status_code == 500 and calls["n"] == 1
    assert RecurringStream.query.count() == 0 and RecurringStreamEvidence.query.count() == 0


def test_candidates_list_review_items_with_evidence_and_no_transaction_ids(client):
    add_rent()
    post(client, "scan", dry_run=False)
    body = client.get("/api/recurring/candidates").get_json()
    assert len(body["candidates"]) == 1
    item = body["candidates"][0]
    assert item["status"] == "proposed" and item["source"] == "detected" and item["evidence_count"] == 3
    assert [e["date"] for e in item["evidence"]] == ["2026-09-21", "2026-08-21", "2026-07-21"]
    assert item["amount_range"] == {"min": "-700.00", "max": "-700.00"}
    assert item["reason_codes"] == ["3_occurrences", "cadence_monthly"]
    assert "secret-" not in str(body) and "transaction_id" not in str(body)

    manual(client)  # manual plans are never "candidates"
    assert len(client.get("/api/recurring/candidates").get_json()["candidates"]) == 1


def test_ignoring_a_candidate_persists_after_every_rescan(client):
    add_rent()
    post(client, "scan", dry_run=False)
    stream_id = client.get("/api/recurring/candidates").get_json()["candidates"][0]["stream_id"]

    decided = post(client, f"streams/{stream_id}/decision", decision="ignored")
    assert decided.status_code == 200 and decided.get_json()["stream"]["status"] == "ignored"
    assert client.get("/api/recurring/candidates").get_json()["candidates"] == []
    assert len(client.get("/api/recurring/candidates?include_ignored=true").get_json()["candidates"]) == 1

    assert post(client, "scan", dry_run=False).get_json()["summary"]["preserved"] == 1
    assert db.session.get(RecurringStream, stream_id).status == "ignored"


def test_confirming_creates_an_upcoming_plan_that_a_rescan_does_not_change(client):
    add_rent()
    post(client, "scan", dry_run=False)
    stream_id = client.get("/api/recurring/candidates").get_json()["candidates"][0]["stream_id"]
    confirmed = post(client, f"streams/{stream_id}/decision", decision="confirmed").get_json()["stream"]
    assert confirmed["status"] == "confirmed"
    client.patch(f"/api/recurring/streams/{stream_id}", json={"amount_cash_delta": "-705.00"})
    post(client, "scan", dry_run=False)
    saved = client.get("/api/recurring/streams?status=confirmed").get_json()["streams"][0]
    assert saved["amount_cash_delta"] == "-705.00"
    assert client.get("/api/recurring/candidates").get_json()["candidates"] == []


# ----------------------------------------------------------------------------- edit / decide / end


def test_patch_updates_fields_and_checks_the_new_account_owner(client):
    stream_id = manual(client).get_json()["stream"]["stream_id"]
    ok = client.patch(
        f"/api/recurring/streams/{stream_id}",
        json={"amount_cash_delta": "-150.00", "cadence": "quarterly", "anchor_date": "2026-12-01", "notes": "n"},
    )
    assert ok.status_code == 200
    stream = ok.get_json()["stream"]
    assert (stream["amount_cash_delta"], stream["cadence"], stream["next_due_date"]) == (
        "-150.00",
        "quarterly",
        "2026-12-01",
    )

    assert client.patch(f"/api/recurring/streams/{stream_id}", json={"account_id": "sav"}).status_code == 200
    assert db.session.get(RecurringStream, stream_id).account_id == "sav"
    foreign = client.patch(f"/api/recurring/streams/{stream_id}", json={"account_id": "bob", "notes": "stolen"})
    assert foreign.status_code == 404
    saved = db.session.get(RecurringStream, stream_id)
    assert saved.account_id == "sav" and saved.notes == "n"  # nothing applied from the rejected request
    assert client.patch(f"/api/recurring/streams/{stream_id}", json={"user_id": "bob"}).status_code == 400
    assert client.patch(f"/api/recurring/streams/{stream_id}", json={"status": "confirmed"}).status_code == 400


def test_decisions_are_validated_and_scoped(client):
    stream_id = manual(client).get_json()["stream"]["stream_id"]
    assert post(client, f"streams/{stream_id}/decision", decision="proposed").status_code == 400
    assert post(client, f"streams/{stream_id}/decision").status_code == 400
    foreign = repo.create_manual(
        "bob", account_id="bob", display_name="x", amount_cash_delta="-1", cadence="monthly", anchor_date="2026-11-01"
    )
    assert post(client, f"streams/{foreign.id}/decision", decision="ignored").status_code == 404
    assert db.session.get(RecurringStream, foreign.id).status == "confirmed"


def test_delete_ends_by_default_hard_deletes_on_request_and_never_touches_transactions(client):
    add_rent()
    stream_id = manual(client).get_json()["stream"]["stream_id"]
    ended = client.delete(f"/api/recurring/streams/{stream_id}")
    assert ended.get_json()["action"] == "ended" and db.session.get(RecurringStream, stream_id).status == "ended"
    assert client.delete(f"/api/recurring/streams/{stream_id}?hard=true").get_json()["action"] == "deleted"
    assert db.session.get(RecurringStream, stream_id) is None
    assert Transaction.query.count() == 3
    assert client.delete("/api/recurring/streams/missing").status_code == 404
