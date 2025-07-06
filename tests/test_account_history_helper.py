import sys
import types
from datetime import date

# ---- Stub Modules for app, extensions, and models ----
app_stub = types.ModuleType("app")
extensions_stub = types.ModuleType("app.extensions")
models_stub = types.ModuleType("app.models")


# ---- Model & DB Stubs ----
class DBSessionStub:
    def __init__(self, results):
        self.results = results
        self.saved = []

    def query(self, *_args, **_kwargs):
        return QueryStub(self.results)

    def bulk_save_objects(self, objs):
        self.saved.extend(objs)

    def commit(self):
        pass


class QueryStub:
    def __init__(self, results):
        self.results = results

    def group_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.results


class AccountHistory:
    def __init__(self, account_id, date, balance):
        self.account_id = account_id
        self.date = date
        self.balance = balance


models_stub.AccountHistory = AccountHistory


class Transaction:
    pass


models_stub.Transaction = Transaction

# ---- Patch sys.modules BEFORE importing the module under test ----
sys.modules["app"] = app_stub
sys.modules["app.extensions"] = extensions_stub
sys.modules["app.models"] = models_stub

# ---- Add the db.session stub ----
RESULTS = [("acc1", date(2024, 1, 1), 15.0), ("acc2", date(2024, 1, 2), -5.0)]
extensions_stub.db = types.SimpleNamespace(session=DBSessionStub(RESULTS))

# ---- NOW Import the helper under test ----
from app.helpers import account_history_helper


# ---- Test ----
def test_update_account_history_creates_account_history():
    # Optionally, re-patch session here too:
    extensions_stub.db.session = DBSessionStub(RESULTS)
    db_session = extensions_stub.db.session
    account_history_helper.update_account_history()
    assert len(db_session.saved) == 2
    assert db_session.saved[0].account_id == "acc1"
    assert db_session.saved[0].balance == 15.0
    assert db_session.saved[1].date == date(2024, 1, 2)
