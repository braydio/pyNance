"""Test suite for `account_history_helper.update_account_history`."""

import os
import sys
import types
from datetime import date
import importlib.util

import pytest

# ---- Stub Modules for app, extensions, and models ----

# Stub app package and submodules
app_stub = types.ModuleType("app")
extensions_stub = types.ModuleType("app.extensions")
models_stub = types.ModuleType("app.models")


# --- DB session stub (to record objects saved) ---
class DBSessionStub:
    """Minimal SQLAlchemy session mock."""

    def __init__(self, results):
        self.results = results
        self.saved = []

    def query(self, *_args, **_kwargs):
        return QueryStub(self.results)

    def bulk_save_objects(self, objs):
        self.saved.extend(objs)

    def commit(self):
        pass  # No-op


# --- Query stub (for group_by/all chaining) ---
class QueryStub:
    def __init__(self, results):
        self.results = results

    def group_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.results


# --- Model stubs ---
class AccountHistory:
    def __init__(self, account_id, date, balance):
        self.account_id = account_id
        self.date = date
        self.balance = balance


models_stub.AccountHistory = AccountHistory


class Transaction:
    account_id = None
    date = None
    amount = None


models_stub.Transaction = Transaction

# ---- Patch sys.modules for backend imports ----
sys.modules.setdefault("app", app_stub)
sys.modules["app.extensions"] = extensions_stub
sys.modules["app.models"] = models_stub

# ---- Stub the results and db session ----
RESULTS = [("acc1", date(2024, 1, 1), 15.0), ("acc2", date(2024, 1, 2), -5.0)]
extensions_stub.db = types.SimpleNamespace(session=DBSessionStub(RESULTS))

# ---- Dynamically import the helper under test ----
MODULE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "backend",
    "app",
    "helpers",
    "account_history_helper.py",
)
spec = importlib.util.spec_from_file_location("account_history_helper", MODULE_PATH)
account_history_helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(account_history_helper)


# ---- Tests ----
def test_update_account_history_creates_account_history():
    """Records returned from the query are saved as AccountHistory objects."""
    db_session = extensions_stub.db.session
    account_history_helper.update_account_history()
    assert len(db_session.saved) == 2
    assert db_session.saved[0].account_id == "acc1"
    assert db_session.saved[0].balance == 15.0
    assert db_session.saved[1].date == date(2024, 1, 2)
