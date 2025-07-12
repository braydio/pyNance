import importlib.util
import os
import sys
import types

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")

sys.modules.pop("app", None)
app_pkg = types.ModuleType("app")
extensions_stub = types.ModuleType("app.extensions")
extensions_stub.db = types.SimpleNamespace(
    commit=lambda: None,
    session=types.SimpleNamespace(add=lambda x: None, commit=lambda: None),
)
app_pkg.extensions = extensions_stub
sys.modules["app"] = app_pkg
sys.modules["app.extensions"] = extensions_stub

spec = importlib.util.spec_from_file_location(
    "app.sql.transaction_rules_logic",
    os.path.join(BASE_BACKEND, "app", "sql", "transaction_rules_logic.py"),
)
trl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trl)


def test_apply_rules_matches():
    rule = types.SimpleNamespace(
        user_id="u1",
        match_criteria={"merchant_name": "Starbucks"},
        action={"category": "Coffee"},
        is_active=True,
    )
    trl.get_applicable_rules = lambda user_id: [rule]
    tx = {"merchant_name": "Starbucks", "amount": 5.0}
    out = trl.apply_rules("u1", tx)
    assert out["category"] == "Coffee"
    assert out["updated_by_rule"] is True
