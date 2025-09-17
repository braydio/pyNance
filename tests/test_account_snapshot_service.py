"""Unit tests for account snapshot service helpers."""

import importlib.util
import os
import sys
import types

import pytest

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)
sys.modules.pop("app", None)

app_pkg = types.ModuleType("app")
app_pkg.__path__ = []
sys.modules["app"] = app_pkg

extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(session=None)
sys.modules["app.extensions"] = extensions_stub

models_stub = types.ModuleType("app.models")
models_stub.Account = type("Account", (), {})
models_stub.AccountSnapshotPreference = type("AccountSnapshotPreference", (), {})
sys.modules["app.models"] = models_stub

finance_stub = types.ModuleType("app.utils.finance_utils")
finance_stub.normalize_account_balance = lambda balance, _: balance
sys.modules["app.utils.finance_utils"] = finance_stub


SERVICE_PATH = os.path.join(BASE_BACKEND, "app", "services", "account_snapshot.py")
spec = importlib.util.spec_from_file_location("account_snapshot_service", SERVICE_PATH)
snapshot_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot_service)


def make_accounts():
    def account(idx, name, balance):
        return types.SimpleNamespace(
            id=idx,
            account_id=f"acc-{idx}",
            name=name,
            institution_name="Bank",
            type="depository",
            subtype="checking",
            link_type="Plaid",
            balance=balance,
            is_hidden=False,
            plaid_account=types.SimpleNamespace(last_refreshed=None),
            teller_account=types.SimpleNamespace(last_refreshed=None),
        )

    return [account(1, "Checking", 150.0), account(2, "Savings", 90.0)]


def make_preference(existing):
    class Preference:
        query = types.SimpleNamespace(
            filter_by=lambda **kwargs: types.SimpleNamespace(first=lambda: existing)
        )

        def __init__(self, user_id, selected_account_ids):
            self.id = 99
            self.user_id = user_id
            self.selected_account_ids = selected_account_ids
            self.created_at = None
            self.updated_at = None

    return Preference


def setup_session(monkeypatch):
    added = []
    commits = []

    def add(obj):
        added.append(obj)

    def commit():
        commits.append(True)

    session = types.SimpleNamespace(add=add, commit=commit)
    monkeypatch.setattr(snapshot_service, "db", types.SimpleNamespace(session=session))
    return added, commits


def test_build_snapshot_payload_creates_preference(monkeypatch):
    accounts = make_accounts()
    monkeypatch.setattr(snapshot_service, "_visible_accounts", lambda: accounts)
    monkeypatch.setattr(
        snapshot_service, "AccountSnapshotPreference", make_preference(None)
    )
    added, commits = setup_session(monkeypatch)

    data = snapshot_service.build_snapshot_payload(user_id="user-x")

    assert data["selected_account_ids"] == ["acc-1", "acc-2"]
    assert len(data["selected_accounts"]) == 2
    assert len(added) == 1
    assert commits  # commit performed for new preference


def test_build_snapshot_payload_sanitizes_selection(monkeypatch):
    accounts = make_accounts()
    monkeypatch.setattr(snapshot_service, "_visible_accounts", lambda: accounts)

    existing = types.SimpleNamespace(
        id=5,
        user_id="user-y",
        selected_account_ids=["acc-1", "ghost"],
        created_at=None,
        updated_at=None,
    )
    Preference = make_preference(existing)
    monkeypatch.setattr(snapshot_service, "AccountSnapshotPreference", Preference)
    added, commits = setup_session(monkeypatch)

    data = snapshot_service.build_snapshot_payload(user_id="user-y")

    assert data["selected_account_ids"] == ["acc-1"]
    assert data["metadata"].get("discarded_ids") == ["ghost"]
    assert existing.selected_account_ids == ["acc-1"]
    assert not added  # no new preference created
    assert commits  # commit from sanitation


def test_update_snapshot_selection_filters_invalid(monkeypatch):
    accounts = make_accounts()
    monkeypatch.setattr(snapshot_service, "_visible_accounts", lambda: accounts)

    existing = types.SimpleNamespace(
        id=7,
        user_id="user-z",
        selected_account_ids=["acc-1"],
        created_at=None,
        updated_at=None,
    )
    Preference = make_preference(existing)
    monkeypatch.setattr(snapshot_service, "AccountSnapshotPreference", Preference)
    added, commits = setup_session(monkeypatch)

    data = snapshot_service.update_snapshot_selection(
        ["acc-1", "acc-2", "ghost", "acc-2"], user_id="user-z"
    )

    assert data["selected_account_ids"] == ["acc-1", "acc-2"]
    assert data["metadata"].get("discarded_ids") == ["ghost"]
    assert existing.selected_account_ids == ["acc-1", "acc-2"]
    assert not added
    assert commits
