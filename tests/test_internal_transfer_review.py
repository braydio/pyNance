"""Transfer Review: owner-scoped scan, evidence payload and safe pair confirmation."""

import os

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from datetime import date, timedelta
from decimal import Decimal

import pytest
from app.extensions import db
from app.models import Account, Transaction
from app.routes.transactions import transactions
from app.services import internal_transfer_review as review
from app.services import recurring_repository as repo
from flask import Flask

TODAY = date.today()


@pytest.fixture()
def app():
    flask_app = Flask(__name__)
    flask_app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(flask_app)
    flask_app.register_blueprint(transactions, url_prefix="/api/transactions")
    with flask_app.app_context():
        db.create_all()
        for account_id, user, name in (
            ("chk", "alice", "Checking"),
            ("sav", "alice", "Savings"),
            ("bob-chk", "bob", "Bob Checking"),
        ):
            db.session.add(
                Account(
                    account_id=account_id,
                    user_id=user,
                    name=name,
                    institution_name="Bank",
                    type="depository",
                    subtype="checking",
                )
            )
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app, monkeypatch):
    monkeypatch.setenv(repo.OWNER_ENV, "alice")
    return app.test_client()


def tx(txid, account, raw, days_ago=1, desc="Transfer", user="alice", provider="plaid", **extra):
    """Add a row; ``raw`` is the stored (Plaid) amount, + outflow / - inflow."""
    row = Transaction(
        transaction_id=txid,
        user_id=user,
        account_id=account,
        date=TODAY - timedelta(days=days_ago),
        amount=Decimal(str(raw)),
        provider=provider,
        description=desc,
        **extra,
    )
    db.session.add(row)
    return row


def seed_pair():
    tx("out", "chk", "200.00", desc="Transfer to savings")
    tx("in", "sav", "-200.00", desc="Transfer from checking")
    db.session.commit()


def scan(client, **params):
    return client.post("/api/transactions/scan-internal", query_string=params)


def test_scan_returns_evidence_pairs_and_no_identifiers(client):
    seed_pair()
    body = scan(client).get_json()
    assert body["status"] == "success" and len(body["pairs"]) == 1
    pair = body["pairs"][0]
    assert pair["left"]["transaction_id"] == "out" and pair["left"]["amount"] == -200.0  # money out first
    assert pair["right"]["transaction_id"] == "in" and pair["right"]["amount"] == 200.0
    assert pair["left"]["account_label"] == "Bank / Checking"
    assert pair["evidence"] == {
        "amount_gap_cents": 0,
        "day_gap": 0,
        "shared_tokens": ["transfer"],
        "transfer_keyword": True,
        "low_confidence": False,
    }
    assert pair["confidence_label"] == "strong"
    assert "user_id" not in str(body) and "match_score" not in str(body)
    assert body["range"]["end"] == TODAY.isoformat() and body["truncated"] is False


def test_scan_is_read_only(client):
    seed_pair()
    scan(client)
    assert {t.is_internal for t in Transaction.query.all()} <= {False, None}


def test_scan_never_crosses_tenants_or_reads_foreign_accounts(client):
    tx("out", "chk", "200.00")
    tx("bob-in", "bob-chk", "-200.00", user="bob")
    tx("alice-row-on-bob-account", "bob-chk", "-200.00", user="alice")  # owner mismatch on the account
    db.session.commit()
    assert scan(client).get_json()["pairs"] == []


def test_scan_fails_closed_without_trusted_owner(app, monkeypatch):
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    seed_pair()
    response = app.test_client().post("/api/transactions/scan-internal")
    assert response.status_code == 503 and response.get_json()["code"] == "owner_not_configured"
    assert "pairs" not in response.get_json()


def test_scan_skips_pending_and_already_internal_rows(client):
    tx("out", "chk", "200.00", pending=True)
    tx("in", "sav", "-200.00")
    tx("out2", "chk", "75.00", is_internal=True)
    tx("in2", "sav", "-75.00")
    db.session.commit()
    assert scan(client).get_json()["pairs"] == []


def test_amount_mismatch_and_same_sign_do_not_pair(client):
    tx("a", "chk", "200.00")
    tx("b", "sav", "-199.00")
    tx("c", "chk", "50.00")
    tx("d", "sav", "50.00")
    db.session.commit()
    assert scan(client).get_json()["pairs"] == []


def test_unknown_sign_manual_rows_are_skipped(client):
    tx("out", "chk", "200.00", provider="manual")
    tx("in", "sav", "-200.00", provider="manual")
    db.session.commit()
    body = scan(client).get_json()
    assert body["pairs"] == [] and body["skipped_unknown_sign"] == 2


def test_same_account_refund_is_not_a_transfer_by_default(client):
    tx("charge", "chk", "30.00", desc="Amazon order")
    tx("refund", "chk", "-30.00", desc="Amazon refund")
    db.session.commit()
    assert scan(client).get_json()["pairs"] == []
    assert scan(client, allow_same_account="true").get_json()["pairs"] == []  # no transfer evidence either


def test_same_account_pair_needs_explicit_opt_in_and_evidence(client):
    tx("out", "chk", "40.00", desc="Transfer correction")
    tx("in", "chk", "-40.00", desc="Transfer correction")
    db.session.commit()
    assert scan(client).get_json()["pairs"] == []
    pairs = scan(client, allow_same_account="true").get_json()["pairs"]
    assert len(pairs) == 1 and pairs[0]["confidence_label"] == "review"


def test_weak_evidence_is_labelled_review_not_strong(client):
    tx("out", "chk", "60.00", desc="Debit 1")
    tx("in", "sav", "-60.00", desc="Credit 9", days_ago=3)
    db.session.commit()
    pair = scan(client).get_json()["pairs"][0]
    assert pair["confidence_label"] == "review" and pair["evidence"]["low_confidence"] is True
    assert pair["evidence"]["day_gap"] == 2


def test_range_validation_and_caps(client):
    assert scan(client, start_date="2024-01-01", end_date="2026-01-01").status_code == 400
    assert scan(client, start_date="2026-02-01", end_date="2026-01-01").status_code == 400
    assert scan(client, start_date="nope").status_code == 400
    assert scan(client, amount_epsilon="x").status_code == 400


def test_large_input_is_cut_off_with_a_truncation_flag(app):
    for i in range(12):
        tx(f"o{i}", "chk", f"{10 + i}.00", days_ago=1, desc="Transfer")
        tx(f"i{i}", "sav", f"-{10 + i}.00", days_ago=1, desc="Transfer")
    db.session.commit()

    capped_rows = review.find_candidates("alice", max_rows=10)
    assert capped_rows["scanned_rows"] == 10 and capped_rows["truncation"]["rows"] is True
    capped_pairs = review.find_candidates("alice", max_pairs=3)
    assert len(capped_pairs["pairs"]) == 3 and capped_pairs["truncation"]["pairs"] is True and capped_pairs["truncated"]
    with pytest.raises(review.OwnerRequired):
        review.find_candidates("")


# ----------------------------------------------------------------------------- confirmation


def confirm(client, txid="out", counterpart="in", **extra):
    body = {"transaction_id": txid, "is_internal": True, "counterpart_transaction_id": counterpart, **extra}
    return client.put("/api/transactions/update", json=body)


def state(txid):
    row = db.session.get(Transaction, Transaction.query.filter_by(transaction_id=txid).one().id)
    return row.is_internal, row.internal_match_id


def test_confirm_marks_both_legs_and_is_replay_safe(client):
    seed_pair()
    assert confirm(client).status_code == 200
    assert state("out") == (True, "in") and state("in") == (True, "out")
    assert confirm(client).status_code == 200  # replay
    assert state("out") == (True, "in") and state("in") == (True, "out")
    assert confirm(client, txid="in", counterpart="out").status_code == 200  # reverse direction replay


def test_confirm_cross_owner_pair_is_403_with_no_partial_change(client):
    tx("out", "chk", "200.00")
    tx("bob-in", "bob-chk", "-200.00", user="bob")
    db.session.commit()
    response = confirm(client, counterpart="bob-in", description="tampered")
    assert response.status_code == 403
    assert state("out") == (False, None) and state("bob-in") == (False, None)
    assert Transaction.query.filter_by(transaction_id="out").one().description == "Transfer"


def test_confirm_foreign_primary_transaction_is_403(client):
    tx("bob-out", "bob-chk", "200.00", user="bob")
    tx("in", "sav", "-200.00")
    db.session.commit()
    assert confirm(client, txid="bob-out").status_code == 403
    assert state("bob-out") == (False, None)


@pytest.mark.parametrize(
    "setup, expected",
    [
        (lambda: (tx("out", "chk", "200.00"), tx("in", "sav", "300.00")), 409),  # same direction
        (lambda: (tx("out", "chk", "200.00", pending=True), tx("in", "sav", "-200.00")), 409),  # pending
        (lambda: (tx("out", "chk", "200.00"), tx("in", "chk", "-200.00")), 400),  # same account, no opt-in
        (lambda: (tx("out", "chk", "200.00", provider="manual"), tx("in", "sav", "-200.00")), 409),  # unknown sign
    ],
)
def test_confirm_rejects_invalid_pairs_without_changes(client, setup, expected):
    setup()
    db.session.commit()
    assert confirm(client).status_code == expected
    assert state("out") == (False, None) and state("in") == (False, None)


def test_confirm_enforces_one_to_one_linkage(client):
    tx("out", "chk", "200.00")
    tx("in", "sav", "-200.00")
    tx("other", "sav", "-200.00", is_internal=True, internal_match_id="somewhere-else")
    db.session.commit()
    assert confirm(client, counterpart="other").status_code == 409
    assert confirm(client).status_code == 200
    tx("late", "sav", "-200.00")
    db.session.commit()
    assert confirm(client, counterpart="late").status_code == 409  # "out" already paired with "in"
    assert state("late") == (False, None)


def test_confirm_missing_counterpart_is_404_and_self_pair_is_400(client):
    seed_pair()
    assert confirm(client, counterpart="ghost").status_code == 404
    assert confirm(client, counterpart="out").status_code == 400


def test_flagging_fails_closed_without_trusted_owner(app, monkeypatch):
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    seed_pair()
    assert confirm(app.test_client()).status_code == 503
    assert state("out") == (False, None)


def test_unconfirm_clears_both_legs(client):
    seed_pair()
    confirm(client)
    response = client.put(
        "/api/transactions/update",
        json={"transaction_id": "out", "is_internal": False, "counterpart_transaction_id": "in"},
    )
    assert response.status_code == 200
    assert state("out") == (False, None) and state("in") == (False, None)
