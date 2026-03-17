import importlib.util
import sys
import types
from pathlib import Path


class _FakeLogger:
    def info(self, *_a, **_k):
        pass

    def warning(self, *_a, **_k):
        pass

    def error(self, *_a, **_k):
        pass


class _FakeSession:
    def __init__(self):
        self.commit_calls = 0
        self.rollback_calls = 0

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1

    def add(self, _obj):
        pass


class _Comparator:
    def in_(self, values):
        return values


class _Account:
    account_id = _Comparator()

    def __init__(self, account_id, user_id="u1"):
        self.account_id = account_id
        self.user_id = user_id


class _PlaidAccount:
    def __init__(self, account_id, item_id, access_token, sync_cursor=None):
        self.account_id = account_id
        self.item_id = item_id
        self.access_token = access_token
        self.sync_cursor = sync_cursor
        self.last_refreshed = None


class _Query:
    def __init__(self, first_obj=None, all_objs=None):
        self._first_obj = first_obj
        self._all_objs = all_objs or []

    def filter_by(self, **kwargs):
        if "account_id" in kwargs:
            target = kwargs["account_id"]
            for obj in self._all_objs:
                if getattr(obj, "account_id", None) == target:
                    return _Query(first_obj=obj, all_objs=self._all_objs)
            return _Query(first_obj=None, all_objs=self._all_objs)
        if "item_id" in kwargs:
            target = kwargs["item_id"]
            matches = [
                o for o in self._all_objs if getattr(o, "item_id", None) == target
            ]
            return _Query(first_obj=matches[0] if matches else None, all_objs=matches)
        return self

    def filter(self, _expr):
        return self

    def first(self):
        return self._first_obj

    def all(self):
        return self._all_objs


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


def _load_module(monkeypatch):
    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "app", app_pkg)

    config_stub = types.ModuleType("app.config")
    config_stub.logger = _FakeLogger()
    config_stub.plaid_client = types.SimpleNamespace(
        transactions_sync=lambda _req: _Resp(
            {
                "added": [],
                "modified": [],
                "removed": [],
                "has_more": False,
                "next_cursor": "cursor-final",
            }
        )
    )
    monkeypatch.setitem(sys.modules, "app.config", config_stub)

    extensions_stub = types.ModuleType("app.extensions")
    extensions_stub.db = types.SimpleNamespace(session=_FakeSession())
    monkeypatch.setitem(sys.modules, "app.extensions", extensions_stub)

    sql_pkg = types.ModuleType("app.sql")
    sql_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "app.sql", sql_pkg)
    models_stub = types.ModuleType("app.models")
    models_stub.Account = _Account
    models_stub.Category = object
    models_stub.PlaidAccount = _PlaidAccount
    models_stub.Transaction = object
    monkeypatch.setitem(sys.modules, "app.models", models_stub)

    tx_rules_stub = types.ModuleType("app.sql.transaction_rules_logic")
    tx_rules_stub.apply_rules = lambda _user_id, tx: tx
    monkeypatch.setitem(sys.modules, "app.sql.transaction_rules_logic", tx_rules_stub)

    account_logic_stub = types.ModuleType("app.sql.account_logic")
    account_logic_stub.detect_internal_transfer = lambda _txn: None
    account_logic_stub.get_or_create_category = lambda *_a, **_k: None
    monkeypatch.setitem(sys.modules, "app.sql.account_logic", account_logic_stub)

    refresh_stub = types.ModuleType("app.sql.refresh_metadata")
    refresh_stub.refresh_or_insert_plaid_metadata = lambda *_a, **_k: None
    monkeypatch.setitem(sys.modules, "app.sql.refresh_metadata", refresh_stub)

    seq_stub = types.ModuleType("app.sql.sequence_utils")
    seq_stub.ensure_transactions_sequence = lambda: None
    monkeypatch.setitem(sys.modules, "app.sql.sequence_utils", seq_stub)

    merchant_stub = types.ModuleType("app.utils.merchant_normalization")
    merchant_stub.resolve_merchant = lambda **_k: types.SimpleNamespace(
        display_name="m", merchant_slug="m"
    )
    monkeypatch.setitem(sys.modules, "app.utils.merchant_normalization", merchant_stub)

    module_path = Path("backend/app/services/plaid_sync.py")
    spec = importlib.util.spec_from_file_location(
        "app.services.plaid_sync", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sync_persists_item_cursor_once_after_pages(monkeypatch):
    module = _load_module(monkeypatch)

    primary_account = _Account("acct-primary")
    sibling_account = _Account("acct-sibling")
    primary_plaid = _PlaidAccount(
        "acct-primary", "item-1", "access", sync_cursor="cursor-old"
    )
    sibling_plaid = _PlaidAccount("acct-sibling", "item-1", "access")

    module.Account.query = _Query(
        first_obj=primary_account, all_objs=[primary_account, sibling_account]
    )
    module.PlaidAccount.query = _Query(
        first_obj=primary_plaid, all_objs=[primary_plaid, sibling_plaid]
    )
    module.TransactionsSyncRequest = lambda **kwargs: kwargs
    module._upsert_transaction = lambda *_a, **_k: None
    module._apply_removed = lambda _removed: 0

    result = module.sync_account_transactions("acct-primary")

    assert result["next_cursor"] == "cursor-final"
    assert primary_plaid.sync_cursor == "cursor-final"
    assert sibling_plaid.sync_cursor == "cursor-final"
    assert primary_plaid.last_refreshed is not None
    assert sibling_plaid.last_refreshed is not None
    assert module.db.session.commit_calls == 2
