"""Tests for safe-to-spend service math and serialization."""

import importlib.util
import os
import sys
import types
from datetime import date
from decimal import Decimal

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(debug=lambda *a, **k: None)
sys.modules["app.config"] = config_stub

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(session=types.SimpleNamespace(query=lambda *a, **k: None))
sys.modules["app.extensions"] = extensions_stub


class Account:
    def __init__(self, account_id="acct", balance=Decimal("0"), account_type="depository", subtype="checking"):
        self.account_id = account_id
        self.balance = balance
        self.type = account_type
        self.subtype = subtype
        self.name = "Checking"
        self.is_hidden = False
        self.is_investment = False

    @property
    def display_name(self):
        return self.name


class Transaction:
    pass


class PlannedBill:
    pass


class PlanningScenario:
    pass


models_stub = types.ModuleType("app.models")
models_stub.Account = Account
models_stub.Transaction = Transaction
models_stub.PlannedBill = PlannedBill
models_stub.PlanningScenario = PlanningScenario
sys.modules["app.models"] = models_stub

utils_pkg = types.ModuleType("app.utils")
sys.modules["app.utils"] = utils_pkg
finance_stub = types.ModuleType("app.utils.finance_utils")
finance_stub.normalize_account_balance = lambda balance, account_type, account_id=None, subtype=None: balance
sys.modules["app.utils.finance_utils"] = finance_stub

SERVICE_PATH = os.path.join(BASE_BACKEND, "app", "services", "safe_to_spend.py")
spec = importlib.util.spec_from_file_location("app.services.safe_to_spend", SERVICE_PATH)
service = importlib.util.module_from_spec(spec)
sys.modules["app.services.safe_to_spend"] = service
spec.loader.exec_module(service)


def _projection(total, bills=(), codes=(), planned=None):
    """A stand-in for ``service._obligation_projection`` with the given reserved total."""

    def fake(as_of, display_end, protection_end, user_id=None):
        fake.protection_end = protection_end
        planned_cents = total if planned is None else planned
        return {
            "total_cents": total,
            "bills": list(bills),
            "needs_review_bills": [],
            "totals": {
                "planned": planned_cents,
                "confirmed": total - planned_cents,
                "provisional": 0,
                "needs_review": 0,
                "protection_reserved": total,
                "display_due": 0,
            },
            "coverage": {
                "recurring_projected": True,
                "codes": list(codes),
                "alternate_scenarios_ignored": 0,
                "skipped": [],
            },
        }

    return fake


def _cash_only(monkeypatch):
    """The stubbed module graph cannot import the classifier; checking accounts are cash."""
    monkeypatch.setattr(service, "_is_cash_account", lambda account: True)


def test_build_safe_to_spend_payload_today(monkeypatch):
    _cash_only(monkeypatch)
    monkeypatch.setattr(service, "_visible_accounts", lambda user_id=None: [Account(balance=Decimal("500.00"))])
    monkeypatch.setattr(
        service, "_obligation_projection", _projection(15_000, [{"name": "Power", "amount_cents": 15_000}])
    )
    monkeypatch.setattr(
        service, "_spent_between", lambda start, end, user_id=None, pending=False: 0 if pending else 2_500
    )
    monkeypatch.setattr(
        service,
        "_payday_prediction",
        lambda as_of, user_id=None: {"next_payday": "2026-07-19", "source": "inferred_stream"},
    )

    payload = service.build_safe_to_spend_payload(
        service.SafeToSpendInputs(as_of=date(2026, 7, 12), buffer_cents=25_000)
    )

    # Posted spending is already inside the balance, so it is shown but not deducted again.
    # Room 10_000 is protected through the day before payday (Jul 12..18 = 7 days).
    assert payload["total_protected_room_cents"] == 10_000
    assert payload["protection_window"]["end"] == "2026-07-18" and payload["protection_window"]["days"] == 7
    assert payload["amount_cents"] == payload["daily_allowance_cents"] == 1_428
    assert payload["components"] == {
        "spendable_cash_cents": 50_000,
        "upcoming_outflows_cents": 15_000,
        "planned_bills_cents": 15_000,
        "confirmed_recurring_cents": 0,
        "provisional_recurring_cents": 0,
        "needs_review_cents": 0,
        "required_buffer_cents": 25_000,
        "spent_today_cents": 2_500,
        "spent_today_included_in_balance": "unknown",
        "pending_cash_outflow_cents": 0,
    }
    assert payload["status"] == "tight"  # $14/day over the protected week
    assert payload["confidence"] == "estimated"  # availability and balance age are unverified
    assert payload["cash_coverage"]["availability_unverified"] == 1


def test_build_safe_to_spend_payload_until_payday_per_day(monkeypatch):
    _cash_only(monkeypatch)
    monkeypatch.setattr(service, "_visible_accounts", lambda user_id=None: [Account(balance=Decimal("300.00"))])
    monkeypatch.setattr(service, "_obligation_projection", _projection(10_000))
    monkeypatch.setattr(service, "_spent_between", lambda start, end, user_id=None, pending=False: 0)
    monkeypatch.setattr(
        service,
        "_payday_prediction",
        lambda as_of, user_id=None: {"next_payday": "2026-07-14", "source": "inferred_stream"},
    )

    payload = service.build_safe_to_spend_payload(
        service.SafeToSpendInputs(mode="until_payday", as_of=date(2026, 7, 12), buffer_cents=5_000)
    )

    assert payload["total_horizon_cents"] == 15_000
    assert payload["amount_cents"] == 7_500  # Jul 12..13 (payday money is not protected cash)
    assert payload["horizon_end"] == "2026-07-13"
    assert payload["display_window"] == {"start": "2026-07-12", "end": "2026-07-13", "days": 2}
    assert payload["confidence"] == "estimated"


AS_OF = date(2026, 10, 17)


def _setup(monkeypatch, payday, cash="1000.00", bills=0):
    _cash_only(monkeypatch)
    monkeypatch.setattr(service, "_visible_accounts", lambda user_id=None: [Account(balance=Decimal(cash))])
    monkeypatch.setattr(service, "_obligation_projection", _projection(bills))
    monkeypatch.setattr(service, "_spent_between", lambda start, end, user_id=None, pending=False: 0)
    prediction = {
        "next_payday": payday,
        "source": "confirmed_stream" if payday else "unresolved",
        "needs_review": False,
    }
    monkeypatch.setattr(service, "_payday_prediction", lambda as_of, user_id=None: prediction)


def _build(mode):
    return service.build_safe_to_spend_payload(service.SafeToSpendInputs(mode=mode, as_of=AS_OF, buffer_cents=0))


def test_windows_with_a_validated_payday_oct_30(monkeypatch):
    _setup(monkeypatch, "2026-10-30")
    today, week, payday = _build("today"), _build("week"), _build("until_payday")
    assert today["display_window"] == {"start": "2026-10-17", "end": "2026-10-17", "days": 1}
    assert (
        today["protection_window"]["end"] == "2026-10-29" and today["protection_window"]["basis"] == "day_before_payday"
    )
    assert week["display_window"]["end"] == "2026-10-23" and week["protection_window"]["end"] == "2026-10-29"
    assert payday["display_window"]["end"] == "2026-10-29"
    # 13 protected days: switching modes with identical evidence never inflates the allowance.
    assert today["amount_cents"] == week["amount_cents"] == payday["amount_cents"] == 100_000 // 13


def test_unverified_payday_uses_a_labelled_14_day_fallback(monkeypatch):
    _setup(monkeypatch, None)
    data = _build("until_payday")
    assert data["protection_window"]["end"] == "2026-10-30" and data["protection_window"]["days"] == 14
    assert (
        data["protection_window"]["basis"] == "fallback_14_day"
        and data["protection_window"]["payday_verified"] is False
    )
    assert data["next_income_date"] is None
    assert any("No validated payday" in w for w in data["warnings"])


def test_week_protects_at_least_its_own_seven_days_when_payday_is_sooner(monkeypatch):
    _setup(monkeypatch, "2026-10-20")
    week, today = _build("week"), _build("today")
    assert week["protection_window"]["end"] == "2026-10-23" and week["protection_window"]["basis"] == "rolling_7_day"
    assert today["protection_window"]["end"] == "2026-10-19"
    assert week["amount_cents"] <= today["amount_cents"]


def test_payday_today_unposted_is_not_cash_and_falls_back(monkeypatch):
    _setup(monkeypatch, "2026-10-17")
    data = _build("today")
    assert data["awaiting_payday_post"] is True
    assert (
        data["protection_window"]["basis"] == "fallback_14_day"
        and data["protection_window"]["payday_verified"] is False
    )
    assert data["confidence"] == "estimated"


def test_bills_use_the_protection_end_and_headline_is_not_total_cash(monkeypatch):
    _setup(monkeypatch, "2026-10-30", cash="1000.00")
    fake = _projection(70_000)
    monkeypatch.setattr(service, "_obligation_projection", fake)
    data = _build("today")
    assert fake.protection_end == date(2026, 10, 29)  # a bill due Oct 21 is reserved even in Today mode
    assert data["total_protected_room_cents"] == 30_000
    assert data["amount_cents"] == 30_000 // 13 and data["amount_cents"] != data["total_protected_room_cents"]


def test_overdraft_and_no_cash_do_not_spend(monkeypatch):
    _setup(monkeypatch, "2026-10-30", cash="-50.00")
    data = _build("today")
    assert data["status"] == "do_not_spend" and data["amount_cents"] == 0 and data["total_protected_room_cents"] == 0


def test_confidence_is_evidence_completeness_not_tightness(monkeypatch):
    _setup(monkeypatch, "2026-10-30", cash="5000.00")
    data = _build("today")
    assert data["status"] == "comfortable"
    assert data["confidence"] == "estimated"  # availability and balance age are unverified
    assert data["calculation_version"] == "2" and data["default_buffer_cents"] == 25_000
