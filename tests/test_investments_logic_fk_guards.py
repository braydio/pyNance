"""Focused tests for investment upsert referential integrity guards."""

import importlib.util
import os
import sys
import types

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")


def _load_logic_module():
    sys.modules.pop("app.sql.investments_logic", None)

    config_stub = types.ModuleType("app.config")
    config_stub.logger = types.SimpleNamespace(
        exception=lambda *a, **k: None,
        error=lambda *a, **k: None,
    )
    sys.modules["app.config"] = config_stub

    events = []

    class SessionStub:
        def merge(self, obj):
            events.append(("merge", obj))
            return obj

        def flush(self):
            events.append(("flush", None))

        def execute(self, stmt):
            events.append(("execute", stmt))

        def commit(self):
            events.append(("commit", None))

        def rollback(self):
            events.append(("rollback", None))

    extensions_stub = types.ModuleType("app.extensions")
    extensions_stub.db = types.SimpleNamespace(session=SessionStub())
    sys.modules["app.extensions"] = extensions_stub

    class Security:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class _Cols:
        account_id = "account_id"
        security_id = "security_id"

    class _Table:
        c = _Cols()

    class InvestmentHolding:
        __table__ = _Table()

    models_stub = types.ModuleType("app.models")
    models_stub.Account = type("Account", (), {})
    models_stub.PlaidAccount = type("PlaidAccount", (), {})
    models_stub.InvestmentHolding = InvestmentHolding
    models_stub.InvestmentTransaction = type("InvestmentTransaction", (), {})
    models_stub.Security = Security
    sys.modules["app.models"] = models_stub

    helpers_stub = types.ModuleType("app.helpers.plaid_helpers")
    helpers_stub.get_investments = lambda _token: {
        "securities": [],
        "holdings": [
            {
                "account_id": "acct-1",
                "security_id": "sec-missing",
                "quantity": 1.5,
                "institution_value": 12.34,
                "iso_currency_code": "USD",
            }
        ],
    }
    sys.modules["app.helpers.plaid_helpers"] = helpers_stub

    spec = importlib.util.spec_from_file_location(
        "app.sql.investments_logic",
        os.path.join(BASE_BACKEND, "app", "sql", "investments_logic.py"),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["app.sql.investments_logic"] = module
    spec.loader.exec_module(module)
    return module, events


def test_upsert_investments_creates_missing_security_before_holding(monkeypatch):
    logic, events = _load_logic_module()

    class FakeInsert:
        excluded = types.SimpleNamespace(
            quantity="quantity",
            cost_basis="cost_basis",
            institution_value="institution_value",
            as_of="as_of",
            raw="raw",
        )

        def values(self, values):
            self.values_payload = values
            return self

        def on_conflict_do_update(self, **kwargs):
            self.conflict_kwargs = kwargs
            return self

    monkeypatch.setattr(
        "sqlalchemy.dialects.postgresql.insert", lambda _table: FakeInsert()
    )

    summary = logic.upsert_investments_from_plaid("user-1", "token-1")

    assert summary == {"securities": 1, "holdings": 1}
    assert [event[0] for event in events] == ["merge", "flush", "execute", "commit"]

    placeholder = events[0][1]
    assert placeholder.security_id == "sec-missing"
    assert placeholder.raw["placeholder_from_holding"] is True
    assert placeholder.raw["holding"]["security_id"] == "sec-missing"
