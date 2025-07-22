import importlib.util
import os
import sys
import types

import pytest

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)

# Stub required modules before importing finance_utils
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(info=lambda *a, **k: None)
sys.modules["app.config"] = config_stub

models_stub = types.ModuleType("app.models")
models_stub.Transaction = type("Transaction", (), {})
sys.modules["app.models"] = models_stub

spec = importlib.util.spec_from_file_location(
    "app.utils.finance_utils",
    os.path.join(BASE_BACKEND, "app", "utils", "finance_utils.py"),
)
finance_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finance_utils)

display_transaction_amount = finance_utils.display_transaction_amount


class DummyTxn:
    def __init__(self, amount, ttype=None):
        self.amount = amount
        self.transaction_type = ttype


@pytest.mark.parametrize(
    "amount,ttype,expected",
    [
        (50, "expense", -50),
        (-30, "income", 30),
        (20, None, -20),
        (-15, None, 15),
    ],
)
def test_display_transaction_amount(amount, ttype, expected):
    txn = DummyTxn(amount, ttype)
    assert display_transaction_amount(txn) == expected
