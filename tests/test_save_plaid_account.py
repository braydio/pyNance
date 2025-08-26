import importlib.util
import os
import sys
"""Tests for saving Plaid account records."""

import types

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")


def load_module(name, path):
    if path.endswith("__init__.py"):
        spec = importlib.util.spec_from_file_location(
            name, path, submodule_search_locations=[os.path.dirname(path)]
        )
    else:
        spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def setup_app(tmp_path):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/test.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    config_stub = types.ModuleType("app.config")
    config_stub.logger = types.SimpleNamespace(
        info=lambda *a, **k: None,
        debug=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        error=lambda *a, **k: None,
    )
    config_stub.plaid_client = None
    config_stub.FILES = {
        "LAST_TX_REFRESH": os.path.join(tmp_path, "last.json"),
        "TRANSACTIONS_RAW_ENRICHED": os.path.join(tmp_path, "enriched.json"),
    }
    sys.modules["app.config"] = config_stub

    env_stub = types.ModuleType("app.config.environment")
    env_stub.TELLER_WEBHOOK_SECRET = "dummy"
    sys.modules["app.config.environment"] = env_stub

    sys.modules.setdefault(
        "flask_cors", types.SimpleNamespace(CORS=lambda *a, **k: None)
    )
    sys.modules.setdefault(
        "flask_migrate", types.SimpleNamespace(Migrate=lambda *a, **k: None)
    )

    helpers_stub = types.ModuleType("app.helpers.plaid_helpers")
    helpers_stub.get_accounts = lambda *a, **k: []
    helpers_stub.get_transactions = lambda *a, **k: []
    sys.modules["app.helpers.plaid_helpers"] = helpers_stub

    normalize_stub = types.ModuleType("app.helpers.normalize")
    normalize_stub.normalize_amount = lambda x: x
    sys.modules["app.helpers.normalize"] = normalize_stub

    utils_stub = types.ModuleType("app.utils.finance_utils")
    utils_stub.display_transaction_amount = lambda txn: (
        txn.amount if hasattr(txn, "amount") else 0
    )
    sys.modules["app.utils.finance_utils"] = utils_stub

    extensions = load_module(
        "app.extensions", os.path.join(BASE_BACKEND, "app", "extensions.py")
    )
    extensions.db.init_app(app)
    return app, extensions


@pytest.fixture()
def db_ctx(tmp_path):
    sys.modules.pop("app.extensions", None)
    sys.modules.pop("app.models", None)
    sys.modules.pop("app.sql", None)
    app, extensions = setup_app(tmp_path)
    with app.app_context():
        models = load_module(
            "app.models", os.path.join(BASE_BACKEND, "app", "models", "__init__.py")
        )
        logic = load_module(
            "app.sql.account_logic",
            os.path.join(BASE_BACKEND, "app", "sql", "account_logic.py"),
        )
        extensions.db.create_all()
        yield extensions.db, models, logic
        extensions.db.drop_all()


def test_save_plaid_account_inserts_and_updates(db_ctx):
    db, models, logic = db_ctx

    # minimal account record to satisfy FK
    acc = models.Account(
        account_id="acct1",
        user_id="u1",
        name="Test",
        type="brokerage",
    )
    db.session.add(acc)
    db.session.commit()

    account = logic.save_plaid_account(
        account_id="acct1",
        item_id="item123",
        access_token="tok1",
        product="investments",
    )
    assert account.id
    assert account.product == "investments"
    assert db.session.query(models.PlaidAccount).count() == 1

    account2 = logic.save_plaid_account(
        account_id="acct1",
        item_id="item123",
        access_token="tok2",
        product="investments",
    )
    assert account2.id == account.id
    assert account2.access_token == "tok2"
    assert db.session.query(models.PlaidAccount).count() == 1
