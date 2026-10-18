"""Real SQL coverage for safe-to-spend provider signs, ownership and route."""

import importlib
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from flask import Flask


@pytest.fixture()
def database():
    """Load real app modules independently of legacy tests' import-time stubs."""
    os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    saved = {key: value for key, value in sys.modules.items() if key == "app" or key.startswith("app.")}
    for key in saved:
        sys.modules.pop(key)
    try:
        db = importlib.import_module("app.extensions").db
        models = importlib.import_module("app.models")
        service = importlib.import_module("app.services.safe_to_spend")
        route = importlib.import_module("app.routes.dashboard")
        app = Flask(__name__)
        app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(app)
        app.register_blueprint(route.dashboard, url_prefix="/api/dashboard")
        with app.app_context():
            db.create_all()
            db.session.add_all(
                [
                    models.Account(account_id="a", user_id="user-a", name="Checking", type="depository", balance=1000),
                    models.Account(account_id="b", user_id="user-b", name="Checking", type="depository", balance=100),
                ]
            )
            db.session.commit()
            yield db, models, service, app.test_client()
            db.session.remove()
            db.drop_all()
    finally:
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                sys.modules.pop(key)
        sys.modules.update(saved)
        sys.path.pop(0)


@pytest.mark.parametrize("provider,expense,income", [("plaid", "42.50", "-1500"), ("manual", "-42.50", "1500")])
def test_provider_signs_and_account_ownership(database, provider, expense, income, monkeypatch):
    db, models, service, _ = database
    for txn_id, amount, day in [("expense", expense, 12), ("income-1", income, 1), ("income-2", income, 8)]:
        db.session.add(
            models.Transaction(
                transaction_id=txn_id,
                account_id="a",
                user_id=None,
                provider=provider,
                amount=Decimal(amount),
                date=date(2026, 7, day),
                description="Payroll" if "income" in txn_id else "Shop",
            )
        )
    db.session.commit()
    assert service._spent_between(date(2026, 7, 1), date(2026, 7, 12), "user-a") == 4250
    assert service._spent_between(date(2026, 7, 1), date(2026, 7, 12), "user-b") == 0
    # Two keyword-matching credits are no longer enough to claim a payday.
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    assert service._next_income_date(date(2026, 7, 12), "user-a") is None
    assert service._next_income_date(date(2026, 7, 12), "user-b") is None


def test_real_safe_to_spend_route(database, monkeypatch):
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    db, models, _, client = database
    scenario = models.PlanningScenario(name="Budget", account_id="a")
    db.session.add(scenario)
    db.session.flush()
    db.session.add(
        models.PlannedBill(scenario_id=scenario.id, name="Power", amount_cents=15000, due_date=date(2026, 7, 12))
    )
    db.session.add(
        models.Transaction(
            transaction_id="expense",
            account_id="a",
            user_id=None,
            provider="plaid",
            amount=Decimal("42.50"),
            date=date(2026, 7, 12),
            description="Shop",
        )
    )
    db.session.commit()
    response = client.get("/api/dashboard/safe-to-spend?user_id=user-a&as_of=2026-07-12")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    components = payload["data"]["components"]
    assert {k: components[k] for k in ("spendable_cash_cents", "upcoming_outflows_cents", "required_buffer_cents")} == {
        "spendable_cash_cents": 100000,
        "upcoming_outflows_cents": 15000,
        "required_buffer_cents": 25000,
    }
    assert components["spent_today_cents"] == 4250  # visible, not subtracted again
    assert payload["data"]["upcoming_bills"][0]["name"] == "Power"


def _pay(db, models, txid, account, day, amount="-1500", **extra):
    db.session.add(
        models.Transaction(
            transaction_id=txid,
            account_id=account,
            user_id=None,
            provider="plaid",
            amount=Decimal(amount),
            date=day,
            description="ACME PAYROLL PPD ID 123",
            personal_finance_category={"primary": "INCOME", "detailed": "INCOME_WAGES"},
            **extra,
        )
    )


def _seed_biweekly(db, models, account="a", prefix="p"):
    for i, day in enumerate([date(2026, 9, 4), date(2026, 9, 18), date(2026, 10, 2), date(2026, 10, 16)]):
        _pay(db, models, f"{prefix}{i}", account, day)


def test_payday_evidence_route_is_owner_scoped_read_only_and_redacted(database, monkeypatch):
    db, models, service, client = database
    _seed_biweekly(db, models, "a", "a")
    _seed_biweekly(db, models, "b", "b")
    db.session.commit()
    before = db.session.query(models.Transaction).count()
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")

    body = client.get("/api/dashboard/payday-evidence?as_of=2026-10-17").get_json()["data"]
    assert body["validated"] is True and body["next_payday"] == "2026-10-30"
    assert body["cadence"] == "biweekly" and body["receipt_count"] == 4
    assert body["payer_label"] == "Acme"
    dumped = str(body).lower()
    for leaked in ("ppd", "123", "a0", "txid", "transaction_id", "user-a", "user-b"):
        assert leaked not in dumped

    # A request cannot choose another owner.
    other = client.get("/api/dashboard/payday-evidence?as_of=2026-10-17&user_id=user-b")
    assert other.status_code == 403
    assert db.session.query(models.Transaction).count() == before


def test_payday_evidence_fails_closed_without_a_configured_owner(database, monkeypatch):
    _, _, _, client = database
    monkeypatch.delenv("PYNANCE_OWNER_USER_ID", raising=False)
    response = client.get("/api/dashboard/payday-evidence")
    assert response.status_code == 503
    assert client.get("/api/dashboard/payday-evidence?as_of=nope").status_code == 400


def test_pending_internal_and_other_owner_credits_never_make_a_payday(database, monkeypatch):
    db, models, service, _ = database
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    _pay(db, models, "ok0", "a", date(2026, 10, 2))
    _pay(db, models, "ok1", "a", date(2026, 10, 16))
    _pay(db, models, "pend", "a", date(2026, 9, 18), pending=True)
    _pay(db, models, "xfer", "a", date(2026, 9, 4), is_internal=True)
    _seed_biweekly(db, models, "b", "b")
    db.session.commit()
    assert service._next_income_date(date(2026, 10, 17), "user-a") is None
    assert service._next_income_date(date(2026, 10, 17), "user-b") is None  # not the configured owner


def test_safe_to_spend_exposes_payday_prediction_metadata(database, monkeypatch):
    db, models, service, client = database
    _seed_biweekly(db, models, "a", "a")
    db.session.commit()
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    data = client.get("/api/dashboard/safe-to-spend?as_of=2026-10-17&user_id=user-a").get_json()["data"]
    assert data["next_income_date"] == "2026-10-30"
    assert data["payday_prediction"]["source"] == "inferred_stream"
    assert "candidates" not in data["payday_prediction"]

    monkeypatch.delenv("PYNANCE_OWNER_USER_ID")
    assert client.get("/api/dashboard/safe-to-spend?as_of=2026-10-17&user_id=user-a").status_code == 503
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    assert client.get("/api/dashboard/safe-to-spend?as_of=2026-10-17&user_id=user-b").status_code == 403


def test_confirmed_income_stream_is_used_when_present(database, monkeypatch):
    db, models, service, _ = database
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    db.session.add(
        models.RecurringStream(
            user_id="user-a",
            account_id="a",
            display_name="Acme Payroll",
            amount_cash_delta=Decimal("1500"),
            cadence="biweekly",
            anchor_date=date(2026, 10, 30),
            status="confirmed",
            source="manual",
            event_role="income",
        )
    )
    db.session.commit()
    prediction = service._payday_prediction(date(2026, 10, 17), "user-a")
    assert prediction["source"] == "confirmed_stream" and prediction["next_payday"] == "2026-10-30"
    assert prediction["needs_review"] is False


def _stream(models, **overrides):
    values = dict(
        user_id="user-a",
        account_id="a",
        display_name="Rent",
        merchant_key="rent",
        amount_cash_delta=Decimal("-700"),
        cadence="monthly",
        anchor_date=date(2026, 7, 21),
        status="confirmed",
        source="manual",
        event_role="ordinary_expense",
    )
    values.update(overrides)
    return models.RecurringStream(**values)


def _payday_stream(models):
    return models.RecurringStream(
        user_id="user-a",
        account_id="a",
        display_name="Acme Payroll",
        amount_cash_delta=Decimal("1500"),
        cadence="biweekly",
        anchor_date=date(2026, 10, 30),
        status="confirmed",
        source="manual",
        event_role="income",
    )


def _safe(client, mode="week"):
    response = client.get(f"/api/dashboard/safe-to-spend?as_of=2026-10-17&mode={mode}")
    assert response.status_code == 200
    return response.get_json()["data"]


def test_confirmed_recurring_debit_reserves_700_once_with_no_planned_bill(database, monkeypatch):
    db, models, _, client = database
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    db.session.add_all([_stream(models), _payday_stream(models)])
    db.session.commit()
    for mode in ("week", "today"):
        data = _safe(client, mode)
        components = data["components"]
        assert components["upcoming_outflows_cents"] == 70_000
        assert components["confirmed_recurring_cents"] == 70_000 and components["planned_bills_cents"] == 0
        assert data["upcoming_bills"][0]["due_date"] == "2026-10-21"
        assert data["upcoming_bills"][0]["status"] == "confirmed"
        assert {"id", "name", "account_id", "amount_cents", "source", "estimated", "reason_codes"} <= set(
            data["upcoming_bills"][0]
        )
    # Today mode reserves the bill but reports nothing due today.
    assert _safe(client, "today")["obligation_coverage"]["display_window_due_cents"] == 0
    assert _safe(client, "today")["obligation_coverage"]["protection_window_reserved_cents"] == 70_000


def test_planned_bill_supersedes_stream_and_alternate_scenario_is_ignored(database, monkeypatch):
    db, models, _, client = database
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    baseline = models.PlanningScenario(name="Budget", account_id="a")
    db.session.add_all([baseline, _stream(models), _payday_stream(models)])
    db.session.flush()
    whatif = models.PlanningScenario(name="What if", account_id="a")
    db.session.add(whatif)
    db.session.flush()
    db.session.add_all(
        [
            models.PlannedBill(scenario_id=baseline.id, name="Rent", amount_cents=70_000, due_date=date(2026, 10, 21)),
            models.PlannedBill(scenario_id=whatif.id, name="Rent", amount_cents=90_000, due_date=date(2026, 10, 21)),
        ]
    )
    db.session.commit()
    data = _safe(client)
    assert data["components"]["upcoming_outflows_cents"] == 70_000  # never $1,400
    assert data["components"]["planned_bills_cents"] == 70_000
    assert data["obligation_coverage"]["alternate_scenarios_ignored"] == 1


def test_ignored_card_transfer_foreign_and_two_cycle_streams_do_not_reserve(database, monkeypatch):
    db, models, _, client = database
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    db.session.add_all(
        [
            models.Account(account_id="card", user_id="user-a", name="Card", type="credit", balance=-50),
            models.Account(account_id="sav", user_id="user-a", name="Savings", type="depository", balance=0),
            _payday_stream(models),
            _stream(models, display_name="Ignored", status="ignored"),
            _stream(models, display_name="Card sub", account_id="card", amount_cash_delta=Decimal("-15")),
            _stream(
                models,
                display_name="To savings",
                event_role="transfer",
                funding_account_id="a",
                destination_account_id="sav",
                amount_cash_delta=Decimal("-200"),
            ),
            _stream(models, display_name="Foreign", user_id="user-b", account_id="b"),
        ]
    )
    cand = _stream(
        models,
        display_name="Gym",
        merchant_key="gym",
        status="proposed",
        source="detected",
        confidence=Decimal("0.900"),
        last_observed=date(2026, 9, 21),
        amount_cash_delta=Decimal("-40"),
    )
    db.session.add(cand)
    db.session.flush()
    for day in (date(2026, 8, 21), date(2026, 9, 21)):
        db.session.add(
            models.RecurringStreamEvidence(
                stream_id=cand.id, observed_at=day, canonical_amount=Decimal("-40"), decision="detected"
            )
        )
    db.session.commit()
    data = _safe(client)
    assert data["components"]["upcoming_outflows_cents"] == 0
    assert data["components"]["needs_review_cents"] == 4_000  # two cycles: visible, never silently debited
    assert data["needs_review_bills"][0]["name"] == "Gym"


def test_three_cycle_high_confidence_candidate_is_a_provisional_reserve(database, monkeypatch):
    db, models, _, client = database
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    cand = _stream(
        models,
        status="proposed",
        source="detected",
        confidence=Decimal("0.920"),
        last_observed=date(2026, 9, 21),
    )
    db.session.add_all([cand, _payday_stream(models)])
    db.session.flush()
    for day in (date(2026, 7, 21), date(2026, 8, 21), date(2026, 9, 21)):
        db.session.add(
            models.RecurringStreamEvidence(
                stream_id=cand.id, observed_at=day, canonical_amount=Decimal("-700"), decision="detected"
            )
        )
    db.session.commit()
    data = _safe(client)
    assert data["components"]["provisional_recurring_cents"] == 70_000
    assert data["upcoming_bills"][0]["status"] == "provisional"
    db.session.refresh(cand)
    assert cand.status == "proposed"  # reserving never confirms the candidate
    # Rejecting it (ignored) takes effect on the very next request.
    cand.status = "ignored"
    db.session.commit()
    assert _safe(client)["components"]["upcoming_outflows_cents"] == 0


def test_coverage_warns_when_history_is_missing(database, monkeypatch):
    _, _, _, client = database
    monkeypatch.setenv("PYNANCE_OWNER_USER_ID", "user-a")
    data = _safe(client)
    assert data["obligation_coverage"]["complete"] is False
    assert "no_transactions" in data["obligation_coverage"]["warning_codes"]
    assert data["confidence"] != "ready"
