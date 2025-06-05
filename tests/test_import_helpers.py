import os
import sys
import types
import importlib.util

# Stub minimal app.config with logger
app_stub = types.ModuleType("app")
config_stub = types.ModuleType("app.config")


class DummyLogger:
    def debug(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass


config_stub.logger = DummyLogger()
sys.modules.setdefault("app", app_stub)
sys.modules["app.config"] = config_stub

MODULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "backend", "app", "helpers", "import_helpers.py"
)
spec = importlib.util.spec_from_file_location("import_helpers", MODULE_PATH)
import_helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_helpers)


def test_import_transactions_from_pdf():
    pdf_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "synchrony_sample.pdf"
    )
    result = import_helpers.import_transactions_from_pdf(pdf_path)
    assert result["status"] == "success"
    assert result["count"] == 3
    first = result["data"][0]
    assert first["name"] == "Amazon Purchase"
    assert first["type"] == "debit"
