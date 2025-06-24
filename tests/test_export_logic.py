import contextlib
import importlib.util
import io
import os
import sys
import types

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

sys.modules.pop("app", None)
app_pkg = types.ModuleType("app")
sys.modules["app"] = app_pkg


# Stub app.extensions.db
class QueryStub:
    def __init__(self, rows):
        self.rows = list(rows)
        self.yield_called = False
        self.all_called = False

    def yield_per(self, chunk_size):
        self.yield_called = True
        self.chunk_size = chunk_size
        return self

    def __iter__(self):
        for row in self.rows:
            yield row

    def all(self):
        self.all_called = True
        return self.rows


# Stub current_app
class DummyApp:
    def app_context(self):
        return contextlib.nullcontext()


# Stub models
class DummyTable:
    def __init__(self, columns):
        self.columns = [types.SimpleNamespace(name=c) for c in columns]


class DummyModel:
    __table__ = DummyTable(["id", "name"])

    def __init__(self, id, name):
        self.id = id
        self.name = name


rows = [DummyModel(i, f"name{i}") for i in range(5)]
query_stub = QueryStub(rows)

db_stub = types.SimpleNamespace(
    session=types.SimpleNamespace(query=lambda model: query_stub)
)
db_stub.session.query = lambda model: query_stub
sys.modules["app.extensions"] = types.SimpleNamespace(db=db_stub)

sys.modules["app.models"] = types.ModuleType("app.models")
app_pkg.models = sys.modules["app.models"]
app_pkg.models.Account = DummyModel
app_pkg.models.Transaction = DummyModel
app_pkg.models.RecurringTransaction = DummyModel

MODULE_PATH = os.path.join(BASE_BACKEND, "app", "sql", "export_logic.py")
spec = importlib.util.spec_from_file_location("export_logic", MODULE_PATH)
export_logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_logic)


def test_generate_csv_bytes_streams():
    csv_io = export_logic.generate_csv_bytes(DummyModel, chunk_size=2)
    assert query_stub.yield_called
    assert not query_stub.all_called
    contents = csv_io.getvalue()
    assert "name4" in contents


def test_export_all_to_csv_streams(tmp_path):
    files = {}

    class DummyFile(io.StringIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def fake_open(filename, mode="r", newline=""):
        f = DummyFile()
        files[filename] = f
        return f

    export_logic.open = fake_open
    export_logic.current_app = DummyApp()
    export_logic.db = db_stub
    export_logic.Account = DummyModel
    export_logic.Transaction = DummyModel
    export_logic.RecurringTransaction = DummyModel

    export_logic.export_all_to_csv(chunk_size=2)

    assert query_stub.yield_called
    assert not query_stub.all_called
    assert files
    assert any("name4" in f.getvalue() for f in files.values())
