"""Test suite for ``account_history_helper.update_account_history``."""

import importlib.util
import os
import sys
import types
from datetime import date

# Stub modules
app_stub = types.ModuleType("app")
extensions_stub = types.ModuleType("app.extensions")
models_stub = types.ModuleType("app.models")


class DBSessionStub:
    """Mimics a minimal SQLAlchemy session for testing."""

    def __init__(self, results):
        self.results = results
        self.saved = []

    def query(self, *_args, **_kwargs):
        """Return a query stub with preset results."""
        return QueryStub(self.results)

    def bulk_save_objects(self, objs):
        """Capture saved objects for assertions."""
        self.saved.extend(objs)

    def commit(self):
        """No-op commit for interface compatibility."""
        pass


class QueryStub:
    """Simple query stub returning predefined results."""

    def __init__(self, results):
        self.results = results

    def group_by(self, *_args, **_kwargs):
        """Return self to allow call chaining."""
        return self

    def all(self):
        """Return the prepared result set."""
        return self.results


class AccountHistory:
    """Lightweight placeholder for the real model."""

    def __init__(self, account_id, date, balance):
        self.account_id = account_id
        self.date = date
        self.balance = balance


models_stub.AccountHistory = AccountHistory


class Transaction:
    """Placeholder transaction model with required fields."""

    account_id = None
    date = None
    amount = None


models_stub.Transaction = Transaction

sys.modules.setdefault("app", app_stub)
sys.modules["app.extensions"] = extensions_stub
sys.modules["app.models"] = models_stub

RESULTS = [("acc1", date(2024, 1, 1), 15.0), ("acc2", date(2024, 1, 2), -5.0)]
extensions_stub.db = types.SimpleNamespace(session=DBSessionStub(RESULTS))

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


def test_update_account_history_creates_account_history():
    """Verify aggregated records are persisted to the session."""

    db_session = extensions_stub.db.session
    account_history_helper.update_account_history()

    assert len(db_session.saved) == 2
    assert db_session.saved[0].account_id == "acc1"
    assert db_session.saved[0].balance == 15.0
    assert db_session.saved[1].date == date(2024, 1, 2)
