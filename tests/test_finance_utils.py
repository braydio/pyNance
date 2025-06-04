import os
import sys
import types
import importlib.util

# Provide stubbed modules so finance_utils can be imported without full app deps
app_stub = types.ModuleType("app")
models_stub = types.ModuleType("app.models")
config_stub = types.ModuleType("app.config")

class Transaction:
    pass

models_stub.Transaction = Transaction
class DummyLogger:
    def info(self, *args, **kwargs):
        pass

config_stub.logger = DummyLogger()

sys.modules.setdefault("app", app_stub)
sys.modules["app.models"] = models_stub
sys.modules["app.config"] = config_stub

module_path = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "utils", "finance_utils.py")
spec = importlib.util.spec_from_file_location("finance_utils", module_path)
finance_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finance_utils)

transform_transaction = finance_utils.transform_transaction

class DummyAccount:
    def __init__(self, type_):
        self.type = type_

class DummyTxn:
    def __init__(self, amount, transaction_type=None, account=None):
        self.amount = amount
        self.transaction_type = transaction_type
        self.account = account

def test_transform_transaction_returns_float():
    txn = DummyTxn(amount=100.0, transaction_type="expense", account=DummyAccount("credit card"))
    result = transform_transaction(txn)
    assert isinstance(result, float)
