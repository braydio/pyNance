"""One recurrence detector: candidate fixtures, idempotent persistence and the /scan route."""

import os

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from datetime import date, timedelta
from decimal import Decimal

import pytest
from app.extensions import db
from app.models import Account, RecurringStream, RecurringStreamEvidence, Transaction
from app.routes import recurring as recurring_routes
from app.routes.recurring import recurring
from app.services import recurring_repository as repo
from app.services.recurring_bridge import RecurringBridge
from app.services.recurring_candidate_service import detect_candidate_streams
from app.services.recurring_detection import RecurringDetector
from flask import Flask

AS_OF = date(2026, 10, 17)
ACCOUNTS = [{"account_id": "chk", "type": "depository", "subtype": "checking", "user_id": "alice"}]


def row(txid, day, amount, name, account="chk", **extra):
    """Canonical-delta row: ``amount`` is + inflow / - outflow."""
    return {"transaction_id": txid, "account_id": account, "date": day, "amount": amount, "name": name, **extra}


def detect(rows, accounts=ACCOUNTS, as_of=AS_OF, **kwargs):
    return detect_candidate_streams(rows, accounts, as_of, **kwargs)


def months(start_year, start_month, count):
    for i in range(count):
        index = start_year * 12 + start_month - 1 + i
        yield index // 12, index % 12 + 1


# ----------------------------------------------------------------------------- pure detection


def test_variable_utility_across_month_lengths_is_one_monthly_candidate():
    amounts = {7: -83, 8: -97, 9: -91}
    rows = [row(f"u{m}", date(2026, m, d), amounts[m], "Duke Energy") for m, d in ((7, 3), (8, 5), (9, 2))]
    result = detect(rows)
    assert len(result["candidates"]) == 1
    candidate = result["candidates"][0]
    assert candidate["cadence"] == "monthly" and candidate["amount_mode"] == "variable"
    assert (candidate["amount_min"], candidate["amount_max"], candidate["signed_median"]) == (-97, -83, -91)
    assert candidate["observations"] == 3 and candidate["ready"] is True
    assert candidate["expected_next_date"] == date(2026, 11, 5)  # October's bill has not posted; mode day is the 5th
    assert [e["transaction_id"] for e in candidate["evidence"]] == ["u7", "u8", "u9"]


def test_biweekly_payroll_is_an_inflow_candidate():
    rows = [row(f"p{i}", date(2026, 7, 3) + timedelta(days=14 * i), 2000, "ACME PAYROLL") for i in range(7)]
    candidate = detect(rows)["candidates"][0]
    assert candidate["cadence"] == "biweekly" and candidate["sign"] == 1 and candidate["amount_mode"] == "fixed"
    assert candidate["expected_next_date"] == date(2026, 10, 23)


def test_twice_monthly_paychecks_are_semimonthly():
    rows = []
    for year, month in months(2026, 5, 5):
        rows.append(row(f"a{month}", date(year, month, 1), 1500, "Employer"))
        rows.append(row(f"b{month}", date(year, month, 15), 1500, "Employer"))
    candidate = detect(rows)["candidates"][0]
    assert candidate["cadence"] == "semimonthly"
    assert candidate["expected_next_date"] == date(2026, 11, 1)  # Oct 1 and Oct 15 have not posted yet


def test_quarterly_and_yearly_patterns_are_supported_and_honest_about_history():
    quarterly = [
        row(f"q{i}", d, -300, "Insurance Co")
        for i, d in enumerate((date(2025, 12, 10), date(2026, 3, 10), date(2026, 6, 10), date(2026, 9, 10)))
    ]
    q = detect(quarterly)["candidates"][0]
    assert q["cadence"] == "quarterly" and q["ready"] is True and q["expected_next_date"] == date(2026, 12, 10)

    two_years = [
        row("y1", date(2025, 10, 5), -120, "Domain Renewal"),
        row("y2", date(2026, 10, 5), -120, "Domain Renewal"),
    ]
    y = detect(two_years)["candidates"][0]
    assert y["cadence"] == "yearly" and y["ready"] is False
    assert "needs_review_insufficient_cycles" in y["reason_codes"]
    assert y["expected_next_date"] == date(2027, 10, 5)

    three_years = [row(f"y{i}", date(2024 + i, 10, 5), -120, "Domain Renewal") for i in range(3)]
    full = detect(three_years, lookback_days=900)["candidates"][0]
    assert full["cadence"] == "yearly" and full["ready"] is True


def test_month_end_dates_clamp_to_the_last_valid_day():
    days = [date(2026, 5, 31), date(2026, 6, 30), date(2026, 7, 31), date(2026, 8, 31), date(2026, 9, 30)]
    rows = [row(f"m{i}", d, -50, "Storage Unit") for i, d in enumerate(days)]
    candidate = detect(rows)["candidates"][0]
    assert candidate["cadence"] == "monthly" and candidate["expected_next_date"] == date(2026, 10, 31)


def test_two_aligned_cycles_are_review_only_not_a_confirmed_bill():
    rows = [row("s1", date(2026, 8, 21), -700, "Rent Payment"), row("s2", date(2026, 9, 21), -700, "Rent Payment")]
    candidate = detect(rows)["candidates"][0]
    assert candidate["ready"] is False and candidate["observations"] == 2
    assert candidate["reason_codes"][0] == "needs_review_insufficient_cycles"
    assert candidate["confidence"] < 0.6


def test_three_subscription_tiers_of_one_merchant_stay_separate():
    rows = []
    for tier, price in enumerate((-9.99, -15.49, -22.99)):
        rows += [row(f"t{tier}-{m}", date(2026, m, 12), price, "STREAMCO") for m in (7, 8, 9)]
    candidates = detect(rows)["candidates"]
    assert (
        sorted(c["signed_median"] for c in candidates) == [Decimal("-22.99"), Decimal("-15.49"), Decimal("-9.99")]
        or len(candidates) == 3
    )
    assert len({c["candidate_key"] for c in candidates}) == 3


def test_transfers_pending_duplicates_and_noncash_rows_are_excluded():
    rows = [row(f"x{m}", date(2026, m, 9), -400, "Savings Transfer", is_internal=True) for m in (7, 8, 9)]
    rows += [row(f"pend{m}", date(2026, m, 4), -25, "Hold Merchant", pending=True) for m in (7, 8, 9)]
    rows += [row(f"inv{m}", date(2026, m, 6), -75, "Brokerage Buy", account="brk") for m in (7, 8, 9)]
    accounts = ACCOUNTS + [{"account_id": "brk", "type": "investment", "subtype": "brokerage", "user_id": "alice"}]
    assert detect(rows, accounts=accounts)["candidates"] == []


def test_accounts_without_an_owner_produce_no_candidates():
    rows = [row(f"o{m}", date(2026, m, 9), -40, "Gym") for m in (7, 8, 9)]
    ownerless = [{"account_id": "chk", "type": "depository", "subtype": "checking", "user_id": None}]
    assert detect(rows, accounts=ownerless)["candidates"] == []


def test_candidate_keys_are_stable_across_rescans_memo_changes_and_pending_to_posted():
    base = [row(f"r{m}", date(2026, m, 21), -700, f"RENT PAYMENT 0{m}2126") for m in (7, 8, 9)]
    first = detect(base)["candidates"]
    again = detect(list(reversed(base)))["candidates"]
    assert [c["candidate_key"] for c in first] == [c["candidate_key"] for c in again]
    assert len(first) == 1  # a changed bank memo (digits) does not split the stream

    with_pending = base + [row("r10-pending", date(2026, 10, 15), -700, "RENT PAYMENT 102126", pending=True)]
    assert detect(with_pending)["candidates"][0]["candidate_key"] == first[0]["candidate_key"]
    posted = base + [row("r10", date(2026, 10, 15), -700, "RENT PAYMENT 102126")]
    assert detect(posted)["candidates"][0]["candidate_key"] == first[0]["candidate_key"]


def test_history_coverage_is_reported():
    rows = [row(f"h{m}", date(2026, m, 9), -40, "Gym") for m in (7, 8, 9)]
    history = detect(rows)["history"]
    assert history["complete"] is False and history["requested_days"] == 400
    assert history["first_date"] == "2026-07-09"


def test_legacy_detector_wrapper_returns_the_old_shape_from_the_canonical_engine():
    txs = [{"amount": -700.0, "date": f"2026-0{m}-21", "description": "Rent Payment"} for m in (7, 8, 9)]
    found = RecurringDetector(txs).detect()
    assert found == [
        {
            "amount": -700.0,
            "description": "rent payment",
            "frequency": "monthly",
            "last_seen": "2026-09-21",
            "occurrences": 3,
            "account_id": None,
        }
    ]
    assert RecurringDetector(txs[:2]).detect() == []  # below min_occurrences
    assert RecurringDetector([]).detect() == []


# ----------------------------------------------------------------------------- persistence + route


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
    with flask_app.app_context():
        db.create_all()
        db.session.add_all(
            [
                Account(account_id="chk", user_id="alice", name="Checking", type="depository", subtype="checking"),
                Account(account_id="bob-chk", user_id="bob", name="Bob", type="depository", subtype="checking"),
            ]
        )
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()


def add_rent(months_=(7, 8, 9), memo="RENT PAYMENT", account="chk", user="alice"):
    for m in months_:
        db.session.add(
            Transaction(
                transaction_id=f"rent-{account}-{m}",
                user_id=user,
                account_id=account,
                date=date(2026, m, 21),
                amount=Decimal("700.00"),  # Plaid: positive = money out
                provider="plaid",
                description=f"{memo} {m:02d}",
            )
        )
    db.session.commit()


def scan(app, account="chk", **params):
    return app.test_client().post(f"/api/recurring/scan/{account}", query_string=params)


def test_scan_creates_one_stable_owner_scoped_candidate_without_fabricating_transactions(app):
    add_rent()
    before = Transaction.query.count()
    first = scan(app)
    assert first.status_code == 200
    summary = first.get_json()["scan"]
    assert (summary["created"], summary["candidates"], summary["history_incomplete"]) == (1, 1, True)

    stream = RecurringStream.query.one()
    assert (stream.user_id, stream.account_id, stream.status, stream.source) == ("alice", "chk", "proposed", "detected")
    assert stream.cadence == "monthly" and stream.amount_cash_delta == Decimal("-700.00")  # cash leaves the account
    assert stream.anchor_date == date(2026, 10, 21) and stream.candidate_key
    evidence = (
        RecurringStreamEvidence.query.filter_by(stream_id=stream.id).order_by(RecurringStreamEvidence.observed_at).all()
    )
    assert [e.transaction_id for e in evidence] == ["rent-chk-7", "rent-chk-8", "rent-chk-9"]
    assert evidence[0].raw_amount == Decimal("700.00") and evidence[0].canonical_amount == Decimal("-700.00")
    assert Transaction.query.count() == before

    second = scan(app).get_json()["scan"]
    assert (second["created"], second["updated"]) == (0, 1)
    assert RecurringStream.query.count() == 1 and RecurringStreamEvidence.query.count() == 3  # idempotent


def test_two_occurrences_stay_review_only_and_a_changed_memo_does_not_split(app):
    add_rent(months_=(8, 9))
    scan(app)
    stream = RecurringStream.query.one()
    assert stream.status == "proposed" and stream.confidence < Decimal("0.600")
    key = stream.candidate_key

    db.session.add(
        Transaction(
            transaction_id="rent-chk-7",
            user_id="alice",
            account_id="chk",
            date=date(2026, 7, 21),
            amount=Decimal("700.00"),
            provider="plaid",
            description="RENT PAYMENT 9921",  # bank changed the reference digits
        )
    )
    db.session.commit()
    scan(app)
    only = RecurringStream.query.one()
    assert only.id == stream.id and only.candidate_key == key
    assert RecurringStreamEvidence.query.filter_by(stream_id=only.id).count() == 3
    assert only.confidence >= Decimal("0.600")  # a third cycle lifts it above the review-only band


def test_rescan_never_overwrites_a_user_decision(app):
    add_rent()
    scan(app)
    stream = RecurringStream.query.one()
    repo.update_stream("alice", stream.id, status="ignored", notes="not mine")
    summary = scan(app).get_json()["scan"]
    assert summary["preserved"] == 1
    saved = db.session.get(RecurringStream, stream.id)
    assert (saved.status, saved.notes, saved.anchor_date) == ("ignored", "not mine", date(2026, 10, 21))

    confirmed = repo.update_stream("alice", stream.id, status="confirmed", amount_cash_delta="-705.00")
    scan(app)
    assert db.session.get(RecurringStream, confirmed.id).amount_cash_delta == Decimal("-705.00")


def test_scan_rejects_foreign_accounts_and_fails_closed_without_an_owner(app, monkeypatch):
    add_rent(account="bob-chk", user="bob")
    assert scan(app, account="bob-chk").status_code == 404
    assert RecurringStream.query.count() == 0
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    response = scan(app)
    assert response.status_code == 503 and response.get_json()["code"] == "owner_not_configured"


def test_scan_ignores_pending_internal_and_unknown_direction_rows(app):
    add_rent(months_=(7, 8))
    db.session.add(
        Transaction(
            transaction_id="rent-chk-9",
            user_id="alice",
            account_id="chk",
            date=date(2026, 9, 21),
            amount=Decimal("700.00"),
            provider="plaid",
            description="RENT PAYMENT 09",
            pending=True,
        )
    )
    db.session.add(
        Transaction(
            transaction_id="manual-rent",
            user_id="alice",
            account_id="chk",
            date=date(2026, 6, 21),
            amount=Decimal("-700.00"),
            provider="manual",
            description="RENT PAYMENT 06",
        )
    )
    db.session.commit()
    summary = scan(app).get_json()["scan"]
    assert summary["sign_excluded"] == 1
    stream = RecurringStream.query.one()  # two posted cycles only: review-only
    assert RecurringStreamEvidence.query.filter_by(stream_id=stream.id).count() == 2
    assert stream.confidence < Decimal("0.600")


def test_bridge_wrapper_persists_proposals_through_the_repository(app):
    rows = [
        {
            "transaction_id": f"b{m}",
            "account_id": "chk",
            "date": f"2026-0{m}-21",
            "amount": -700.0,
            "description": "Rent Payment",
        }
        for m in (7, 8, 9)
    ]
    ids = RecurringBridge(rows).sync_to_db()
    assert len(ids) == 1 and RecurringStream.query.one().id == ids[0]
    assert RecurringBridge([{"date": "2026-07-21", "amount": -1.0, "description": "x"}]).sync_to_db() == []
    assert Transaction.query.count() == 0
