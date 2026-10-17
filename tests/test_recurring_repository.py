"""Owner-scoped recurring streams: repository, legacy routes and the legacy-row migration."""

import importlib.util
import os

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from datetime import date, timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from app.extensions import db
from app.models import Account, RecurringStream, RecurringTransaction, Transaction
from app.routes.recurring import recurring
from app.services import recurring_repository as repo
from flask import Flask

TODAY = date(2026, 10, 17)


@pytest.fixture()
def app():
    flask_app = Flask(__name__)
    flask_app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(flask_app)
    flask_app.register_blueprint(recurring, url_prefix="/api/recurring")
    with flask_app.app_context():
        db.create_all()
        db.session.add_all(
            [
                Account(account_id="chk", user_id="alice", name="Checking", type="depository", subtype="checking"),
                Account(account_id="chk2", user_id="alice", name="Savings", type="depository", subtype="savings"),
                Account(account_id="bob-chk", user_id="bob", name="Bob", type="depository", subtype="checking"),
            ]
        )
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def owner(monkeypatch):
    monkeypatch.setenv(repo.OWNER_ENV, "alice")
    return "alice"


@pytest.fixture()
def client(app):
    return app.test_client()


def _manual(**overrides):
    fields = dict(
        account_id="chk",
        display_name="Duke Energy",
        amount_cash_delta="-142.37",
        amount_mode="variable",
        cadence="monthly",
        anchor_date="2026-11-03",
    )
    fields.update(overrides)
    return repo.create_manual("alice", **fields)


def test_manual_stream_needs_no_transaction_and_keeps_cents(app):
    stream = _manual()
    assert Transaction.query.count() == 0
    saved = db.session.get(RecurringStream, stream.id)
    assert saved.amount_cash_delta == Decimal("-142.37") and saved.amount_mode == "variable"
    assert saved.status == "confirmed" and saved.source == "manual" and saved.confirmed_at is not None
    assert saved.merchant_key == "duke energy"
    assert repo.serialize(saved)["amount_cash_delta"] == "-142.37"


def test_foreign_or_missing_account_is_rejected_without_mutation(app):
    for account_id in ("bob-chk", "nope"):
        with pytest.raises(repo.AccountNotAvailable):
            _manual(account_id=account_id)
    assert RecurringStream.query.count() == 0
    with pytest.raises(repo.AccountNotAvailable):
        repo.list_streams("alice", account_id="bob-chk")


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount_cash_delta": "abc"},
        {"amount_cash_delta": "NaN"},
        {"cadence": "fortnightly"},
        {"anchor_date": "soon"},
        {"display_name": "  "},
        {"amount_mode": "sometimes"},
    ],
)
def test_invalid_input_never_writes(app, overrides):
    with pytest.raises(repo.ValidationFailed):
        _manual(**overrides)
    assert RecurringStream.query.count() == 0


def test_streams_are_owner_scoped_and_one_merchant_can_have_many_plans(app):
    a = _manual()
    b = _manual(amount_cash_delta="-20.00", amount_mode="fixed", display_name="Duke Energy")
    assert a.id != b.id
    assert len(repo.list_streams("alice", account_id="chk")) == 2
    assert repo.list_streams("bob") == []
    with pytest.raises(repo.StreamNotFound):
        repo.get_stream("bob", a.id)
    with pytest.raises(repo.StreamNotFound):
        repo.update_stream("bob", a.id, notes="mine now")
    with pytest.raises(repo.StreamNotFound):
        repo.delete_or_end_stream("bob", a.id)
    assert db.session.get(RecurringStream, a.id).status == "confirmed"


def test_update_and_end_stream(app):
    stream = _manual()
    repo.update_stream("alice", stream.id, amount_cash_delta=Decimal("-150.005"), cadence="bi-weekly", notes="x")
    saved = db.session.get(RecurringStream, stream.id)
    assert saved.amount_cash_delta == Decimal("-150.00") and saved.cadence == "biweekly"  # banker's rounding
    with pytest.raises(repo.ValidationFailed):
        repo.update_stream("alice", stream.id, user_id="bob")  # unknown/forbidden field
    assert repo.delete_or_end_stream("alice", stream.id) == "ended"
    assert db.session.get(RecurringStream, stream.id).status == "ended"
    assert repo.delete_or_end_stream("alice", stream.id, hard=True) == "deleted"
    assert db.session.get(RecurringStream, stream.id) is None


def test_trusted_owner_fails_closed_when_unset(monkeypatch):
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    with pytest.raises(repo.OwnerNotConfigured):
        repo.trusted_owner_id()
    monkeypatch.setenv(repo.OWNER_ENV, "  ")
    with pytest.raises(repo.OwnerNotConfigured):
        repo.trusted_owner_id()


def test_next_due_date_cadences():
    def stream(cadence, anchor, status="confirmed"):
        return RecurringStream(cadence=cadence, anchor_date=anchor, status=status)

    assert repo.next_due_date(stream("monthly", date(2026, 10, 20)), TODAY) == date(2026, 10, 20)
    assert repo.next_due_date(stream("monthly", date(2026, 8, 31)), TODAY) == date(2026, 10, 31)
    assert repo.next_due_date(stream("weekly", date(2026, 10, 1)), TODAY) == date(2026, 10, 22)
    assert repo.next_due_date(stream("once", date(2026, 10, 1)), TODAY) is None
    assert repo.next_due_date(stream("semimonthly", date(2026, 9, 1)), TODAY) == date(2026, 11, 1)
    assert repo.next_due_date(stream("semimonthly", date(2026, 9, 1)), date(2026, 10, 2)) == date(2026, 10, 16)
    assert repo.next_due_date(stream("monthly", date(2026, 11, 1), "ended"), TODAY) is None


def test_detector_hit_becomes_a_proposal_not_a_fabricated_transaction(app):
    from app.sql.recurring_logic import upsert_recurring

    first = upsert_recurring("Netflix", -15.49, "monthly", date(2026, 11, 5), 0.4, "chk")
    again = upsert_recurring("Netflix", -15.49, "monthly", date(2026, 11, 6), 0.6, "chk")
    assert first == again
    assert Transaction.query.count() == 0 and RecurringTransaction.query.count() == 0
    stream = db.session.get(RecurringStream, first)
    assert (stream.status, stream.source, stream.user_id) == ("proposed", "detected", "alice")
    assert stream.anchor_date == date(2026, 11, 6) and stream.confidence == Decimal("0.600")

    repo.update_stream("alice", first, status="ignored")
    upsert_recurring("Netflix", -15.49, "monthly", date(2026, 12, 1), 0.9, "chk")
    assert db.session.get(RecurringStream, first).status == "ignored"  # a user decision is never overwritten
    assert db.session.get(RecurringStream, first).anchor_date == date(2026, 11, 6)


# ----------------------------------------------------------------------------- legacy routes


def test_legacy_put_creates_a_stream_from_explicit_fields_and_ignores_payload_user(client, owner):
    payload = {
        "description": "Duke Energy",
        "amount": -142.37,
        "frequency": "monthly",
        "next_due_date": "2026-11-03",
        "notes": "variable",
        "user_id": "bob",
    }
    response = client.put("/api/recurring/accounts/chk/recurringTx", json=payload)
    assert response.status_code == 200
    assert response.get_json() == {"status": "success", "message": "Recurring transaction saved."}
    stream = RecurringStream.query.one()
    assert (stream.user_id, stream.account_id, stream.amount_cash_delta) == ("alice", "chk", Decimal("-142.37"))

    payload["notes"] = "changed"
    assert client.put("/api/recurring/accounts/chk/recurringTx", json=payload).status_code == 200
    assert RecurringStream.query.count() == 1 and RecurringStream.query.one().notes == "changed"


def test_legacy_put_on_foreign_account_is_404_and_writes_nothing(client, owner):
    response = client.put("/api/recurring/accounts/bob-chk/recurringTx", json={"description": "Rent", "amount": -900})
    assert response.status_code == 404 and response.get_json()["code"] == "account_not_found"
    assert RecurringStream.query.count() == 0


def test_legacy_put_requires_fields_or_a_real_owned_transaction(client, owner):
    assert client.put("/api/recurring/accounts/chk/recurringTx", json={"frequency": "monthly"}).status_code == 400
    assert client.put("/api/recurring/accounts/chk/recurringTx", json={"tx_id": "ghost"}).status_code == 404

    db.session.add(
        Transaction(
            transaction_id="t1",
            user_id="alice",
            account_id="chk",
            date=TODAY,
            amount=Decimal("1850.00"),
            provider="plaid",
            description="LANDLORD",
        )
    )
    db.session.add(
        Transaction(
            transaction_id="t-manual",
            user_id="alice",
            account_id="chk",
            date=TODAY,
            amount=Decimal("-5.00"),
            provider="manual",
            description="mystery",
        )
    )
    db.session.commit()
    assert client.put("/api/recurring/accounts/chk/recurringTx", json={"tx_id": "t1"}).status_code == 200
    stream = RecurringStream.query.one()
    assert stream.amount_cash_delta == Decimal("-1850.00") and stream.display_name == "LANDLORD"
    assert client.put("/api/recurring/accounts/chk/recurringTx", json={"tx_id": "t-manual"}).status_code == 400


def test_mutations_fail_closed_without_a_configured_owner(client, monkeypatch):
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    response = client.put("/api/recurring/accounts/chk/recurringTx", json={"description": "x", "amount": -1})
    assert response.status_code == 503 and response.get_json()["code"] == "owner_not_configured"
    assert (
        client.delete("/api/recurring/accounts/chk/recurringTx", json={"description": "x", "amount": -1}).status_code
        == 503
    )
    assert RecurringStream.query.count() == 0


def test_legacy_delete_ends_one_match_and_409s_on_ambiguity(client, owner):
    _manual()
    body = {"description": "Duke Energy", "amount": -142.37}
    assert client.delete("/api/recurring/accounts/chk/recurringTx", json={"description": "x"}).status_code == 400
    assert (
        client.delete("/api/recurring/accounts/chk/recurringTx", json={"description": "Nope", "amount": 1}).status_code
        == 404
    )
    _manual(account_id="chk")  # second identical plan
    response = client.delete("/api/recurring/accounts/chk/recurringTx", json=body)
    assert response.status_code == 409 and response.get_json()["code"] == "ambiguous_match"
    assert {s.status for s in RecurringStream.query.all()} == {"confirmed"}

    repo.delete_or_end_stream("alice", RecurringStream.query.first().id)
    response = client.delete("/api/recurring/accounts/chk/recurringTx", json=body)
    assert response.status_code == 200
    assert {s.status for s in RecurringStream.query.all()} == {"ended"}


def test_legacy_get_returns_confirmed_streams_due_within_a_week_for_the_owner_only(client, owner):
    soon = date.today() + timedelta(days=3)
    later = date.today() + timedelta(days=20)
    _manual(anchor_date=soon.isoformat())
    _manual(display_name="Later", anchor_date=later.isoformat())
    _manual(display_name="Ignored", anchor_date=soon.isoformat(), status="ignored")
    repo.create_manual(
        "bob", account_id="bob-chk", display_name="Bob rent", amount_cash_delta="-1", cadence="monthly",
        anchor_date=soon.isoformat(),
    )  # fmt: skip
    response = client.get("/api/recurring/chk/recurring")
    assert response.status_code == 200
    body = response.get_json()
    user = [r for r in body["reminders"] if r["source"] == "user"]
    assert [r["description"] for r in user] == ["Duke Energy"]
    assert user[0]["amount"] == -142.37 and user[0]["frequency"] == "monthly" and user[0]["days_until_due"] == 3
    assert body["streams_available"] is True
    assert client.get("/api/recurring/bob-chk/recurring").get_json()["reminders"] == []


# ----------------------------------------------------------------------------- migration


def _load_migration(filename="b7d2e4f6a8c1_recurring_streams.py"):
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "migrations", "versions", filename)
    spec = importlib.util.spec_from_file_location("recurring_streams_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tx(txid, account, amount, provider="plaid", desc="LANDLORD"):
    return Transaction(
        transaction_id=txid, user_id="alice", account_id=account, date=TODAY, amount=Decimal(amount),
        provider=provider, description=desc,
    )  # fmt: skip


def test_migration_creates_tables_and_copies_only_valid_legacy_rows(app):
    migration = _load_migration()
    db.session.add_all(
        [
            _tx("ok", "chk", "1850.00"),
            _tx("manual", "chk", "-10.00", provider="manual"),
            _tx("odd-cadence", "chk", "9.99", desc="WEIRD"),
            _tx("ownerless", "bob-chk", "5.00"),
        ]
    )
    db.session.flush()
    for txid, account, freq in (
        ("ok", "chk", "monthly"),
        ("manual", "chk", "monthly"),
        ("odd-cadence", "chk", "fortnightly"),
        ("ownerless", "bob-chk", "monthly"),
    ):
        db.session.add(
            RecurringTransaction(transaction_id=txid, account_id=account, frequency=freq, next_due_date=TODAY)
        )
    db.session.commit()
    db.session.get(Account, "bob-chk").user_id = None
    db.session.commit()

    db.session.execute(sa.text("DROP TABLE recurring_stream_evidence"))
    db.session.execute(sa.text("DROP TABLE recurring_streams"))
    db.session.commit()
    legacy_before = RecurringTransaction.query.count()

    candidate_migration = _load_migration("c4f8a1d3e5b7_recurring_stream_candidate_key.py")
    connection = db.engine.connect()
    with Operations.context(MigrationContext.configure(connection)):
        migration.upgrade()
        migration.upgrade()  # idempotent: second run copies nothing new
    connection.commit()
    connection.close()
    # The candidate_key revision is a no-op when the column already exists (fresh create_all schemas).
    connection = db.engine.connect()
    with Operations.context(MigrationContext.configure(connection)):
        candidate_migration.upgrade()
    connection.commit()
    connection.close()
    assert "candidate_key" in {c["name"] for c in sa.inspect(db.engine).get_columns("recurring_streams")}
    role_migration = _load_migration("d5a9b2c7e1f3_recurring_stream_event_role.py")
    connection = db.engine.connect()
    with Operations.context(MigrationContext.configure(connection)):
        role_migration.upgrade()
    connection.commit()
    connection.close()
    assert {"event_role", "funding_account_id", "destination_account_id"} <= {
        c["name"] for c in sa.inspect(db.engine).get_columns("recurring_streams")
    }

    streams = RecurringStream.query.all()
    assert len(streams) == 1
    assert (streams[0].source, streams[0].status, streams[0].amount_cash_delta) == (
        "legacy",
        "confirmed",
        Decimal("-1850.00"),
    )
    assert streams[0].user_id == "alice" and streams[0].cadence == "monthly" and streams[0].anchor_date == TODAY
    assert RecurringTransaction.query.count() == legacy_before  # legacy table untouched
    assert Transaction.query.count() == 4

    connection = db.engine.connect()
    with Operations.context(MigrationContext.configure(connection)):
        migration.downgrade()
    connection.commit()
    connection.close()
    tables = set(sa.inspect(db.engine).get_table_names())
    assert "recurring_streams" not in tables and "recurring_transactions" in tables
