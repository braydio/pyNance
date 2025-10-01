"""Tests for internal transfer detection logic."""

import importlib.util
import os
import sys
import types
from datetime import datetime, timezone
from decimal import Decimal

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)

# Stub required modules before importing account_logic and models
config_stub = types.ModuleType("app.config")
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
    debug=lambda *a, **k: None,
)
config_stub.FILES = {
    "LAST_TX_REFRESH": "last.json",
    "TRANSACTIONS_RAW_ENRICHED": "enriched.json",
}
sys.modules["app.config"] = config_stub

app_pkg = types.ModuleType("app")
app_pkg.config = config_stub
app_pkg.__path__ = []
sys.modules["app"] = app_pkg

helpers_norm = types.ModuleType("app.helpers.normalize")
helpers_norm.normalize_amount = lambda x: Decimal(
    str((x.get("amount") if isinstance(x, dict) else x))
).quantize(Decimal("0.01"))
sys.modules["app.helpers.normalize"] = helpers_norm

plaid_helpers = types.ModuleType("app.helpers.plaid_helpers")
plaid_helpers.get_accounts = lambda *a, **k: []
plaid_helpers.get_transactions = lambda *a, **k: []
sys.modules["app.helpers.plaid_helpers"] = plaid_helpers

transaction_rules_logic = types.ModuleType("app.sql.transaction_rules_logic")
transaction_rules_logic.apply_rules = lambda user_id, tx: tx
sys.modules["app.sql.transaction_rules_logic"] = transaction_rules_logic

refresh_metadata = types.ModuleType("app.sql.refresh_metadata")
refresh_metadata.refresh_or_insert_plaid_metadata = lambda *a, **k: None
sys.modules["app.sql.refresh_metadata"] = refresh_metadata
sql_pkg = types.ModuleType("app.sql")
sql_pkg.transaction_rules_logic = transaction_rules_logic
sql_pkg.refresh_metadata = refresh_metadata
sys.modules["app.sql"] = sql_pkg
app_pkg.sql = sql_pkg

utils_pkg = types.ModuleType("app.utils")
finance_utils = types.ModuleType("app.utils.finance_utils")
finance_utils.display_transaction_amount = lambda txn: txn.amount
sys.modules["app.utils.finance_utils"] = finance_utils
utils_pkg.finance_utils = finance_utils
sys.modules["app.utils"] = utils_pkg
app_pkg.utils = utils_pkg

plaid_stub = types.ModuleType("plaid")


class ApiException(Exception):
    pass


plaid_stub.ApiException = ApiException
sys.modules["plaid"] = plaid_stub

extensions = types.ModuleType("app.extensions")
db = SQLAlchemy()
extensions.db = db
sys.modules["app.extensions"] = extensions
app_pkg.extensions = extensions

# Load models and account_logic modules
spec_models = importlib.util.spec_from_file_location(
    "app.models",
    os.path.join(BASE_BACKEND, "app", "models", "__init__.py"),
    submodule_search_locations=[os.path.join(BASE_BACKEND, "app", "models")],
)
models = importlib.util.module_from_spec(spec_models)
sys.modules["app.models"] = models
spec_models.loader.exec_module(models)
app_pkg.models = models

spec_logic = importlib.util.spec_from_file_location(
    "app.sql.account_logic",
    os.path.join(BASE_BACKEND, "app", "sql", "account_logic.py"),
)
account_logic = importlib.util.module_from_spec(spec_logic)
spec_logic.loader.exec_module(account_logic)
sql_pkg.account_logic = account_logic

spec_routes = importlib.util.spec_from_file_location(
    "app.routes.transactions",
    os.path.join(BASE_BACKEND, "app", "routes", "transactions.py"),
)
transactions_routes = importlib.util.module_from_spec(spec_routes)
spec_routes.loader.exec_module(transactions_routes)


def test_detect_internal_transfer_marks_both_transactions():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        acc1 = models.Account(account_id="A1", user_id="u1", name="Checking")
        acc2 = models.Account(account_id="A2", user_id="u1", name="Credit Card")
        db.session.add_all([acc1, acc2])
        t1 = models.Transaction(
            transaction_id="T1",
            account_id="A1",
            user_id="u1",
            amount=-100.0,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            description="Payment to Credit Card",
        )
        t2 = models.Transaction(
            transaction_id="T2",
            account_id="A2",
            user_id="u1",
            amount=100.0,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            description="Payment from Checking",
        )
        db.session.add_all([t1, t2])
        db.session.commit()

        account_logic.detect_internal_transfer(t1)
        db.session.commit()

        assert t1.is_internal is True
        assert t2.is_internal is True
        assert t1.internal_match_id == "T2"
        assert t2.internal_match_id == "T1"


def test_detect_internal_transfer_without_description_match():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        acc1 = models.Account(account_id="B1", user_id="u1", name="Checking")
        acc2 = models.Account(account_id="B2", user_id="u1", name="Savings")
        db.session.add_all([acc1, acc2])
        t1 = models.Transaction(
            transaction_id="X1",
            account_id="B1",
            user_id="u1",
            amount=-50.0,
            date=datetime(2024, 2, 1, tzinfo=timezone.utc),
            description="Zelle transfer",
        )
        t2 = models.Transaction(
            transaction_id="X2",
            account_id="B2",
            user_id="u1",
            amount=50.0,
            date=datetime(2024, 2, 1, tzinfo=timezone.utc),
            description="Incoming",
        )
        db.session.add_all([t1, t2])
        db.session.commit()

        account_logic.detect_internal_transfer(t1)
        db.session.commit()

        assert t1.is_internal is True
        assert t2.is_internal is True
        assert t1.internal_match_id == "X2"
        assert t2.internal_match_id == "X1"


def test_scan_internal_transfers_endpoint():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    db.init_app(app)
    app.register_blueprint(transactions_routes.transactions, url_prefix="/transactions")
    with app.app_context():
        db.create_all()
        acc1 = models.Account(account_id="C1", user_id="u1", name="Checking")
        acc2 = models.Account(account_id="C2", user_id="u1", name="Savings")
        db.session.add_all([acc1, acc2])
        t1 = models.Transaction(
            transaction_id="Y1",
            account_id="C1",
            user_id="u1",
            amount=-25.0,
            date=datetime(2024, 3, 1, tzinfo=timezone.utc),
            description="Transfer out",
        )
        t2 = models.Transaction(
            transaction_id="Y2",
            account_id="C2",
            user_id="u1",
            amount=25.0,
            date=datetime(2024, 3, 1, tzinfo=timezone.utc),
            description="Transfer in",
        )
        db.session.add_all([t1, t2])
        db.session.commit()

        client = app.test_client()
        res = client.post("/transactions/scan-internal")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["pairs"]) == 1
        assert data["pairs"][0]["transaction_id"] == "Y1"
        assert models.Transaction.query.filter_by(is_internal=True).count() == 0
