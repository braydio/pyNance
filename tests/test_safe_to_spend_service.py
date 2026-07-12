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
finance_stub.normalize_account_balance = lambda balance, account_type, account_id=None: balance
sys.modules["app.utils.finance_utils"] = finance_stub

SERVICE_PATH = os.path.join(BASE_BACKEND, "app", "services", "safe_to_spend.py")
spec = importlib.util.spec_from_file_location("app.services.safe_to_spend", SERVICE_PATH)
service = importlib.util.module_from_spec(spec)
sys.modules["app.services.safe_to_spend"] = service
spec.loader.exec_module(service)


def test_build_safe_to_spend_payload_today(monkeypatch):
    monkeypatch.setattr(service, "_visible_accounts", lambda user_id=None: [Account(balance=Decimal("500.00"))])
    monkeypatch.setattr(
        service,
        "_upcoming_bill_payload",
        lambda as_of, horizon_end, user_id=None: (15_000, [{"name": "Power", "amount_cents": 15_000}]),
    )
    monkeypatch.setattr(service, "_spent_between", lambda start, end, user_id=None: 2_500)
    monkeypatch.setattr(service, "_next_income_date", lambda as_of, user_id=None: date(2026, 7, 19))

    payload = service.build_safe_to_spend_payload(
        service.SafeToSpendInputs(as_of=date(2026, 7, 12), buffer_cents=25_000)
    )

    assert payload["amount_cents"] == 7_500
    assert payload["components"] == {
        "spendable_cash_cents": 50_000,
        "upcoming_outflows_cents": 15_000,
        "required_buffer_cents": 25_000,
        "spent_today_cents": 2_500,
    }
    assert payload["status"] == "comfortable"
    assert payload["confidence"] == "ready"


def test_build_safe_to_spend_payload_until_payday_per_day(monkeypatch):
    monkeypatch.setattr(service, "_visible_accounts", lambda user_id=None: [Account(balance=Decimal("300.00"))])
    monkeypatch.setattr(service, "_upcoming_bill_payload", lambda as_of, horizon_end, user_id=None: (10_000, []))
    monkeypatch.setattr(service, "_spent_between", lambda start, end, user_id=None: 0)
    monkeypatch.setattr(service, "_next_income_date", lambda as_of, user_id=None: date(2026, 7, 14))

    payload = service.build_safe_to_spend_payload(
        service.SafeToSpendInputs(mode="until_payday", as_of=date(2026, 7, 12), buffer_cents=5_000)
    )

    assert payload["total_horizon_cents"] == 15_000
    assert payload["amount_cents"] == 5_000
    assert payload["horizon_end"] == "2026-07-14"
    assert payload["confidence"] == "estimated"
