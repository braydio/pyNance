"""Unit tests for :func:`save_plaid_item`."""
# mypy: ignore-errors
# pylint: disable=all

import importlib.util
import os
import sys
import types

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")

config_stub = types.ModuleType("app.config")
config_stub.FILES = {
    "LAST_TX_REFRESH": "tmp.json",
    "TRANSACTIONS_RAW_ENRICHED": "tmp2.json",
}
config_stub.logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    debug=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    error=lambda *a, **k: None,
)
config_stub.FLASK_ENV = "test"
config_stub.plaid_client = None
sys.modules["app.config"] = config_stub


def load_module(name, path):
    """Import a module from a path and register it in ``sys.modules``."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def setup_app(tmp_path):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/test.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    extensions = load_module(
        "app.extensions", os.path.join(BASE_BACKEND, "app", "extensions.py")
    )
    extensions.db.init_app(app)
    return app, extensions


@pytest.fixture()
def db_ctx(tmp_path):
    app, extensions = setup_app(tmp_path)
    with app.app_context():
        models = load_module(
            "app.models", os.path.join(BASE_BACKEND, "app", "models.py")
        )
        # ensure config stub is present for account_logic imports
        sys.modules["app.config"] = config_stub
        helpers_pkg = types.ModuleType("app.helpers")
        normalize_mod = types.ModuleType("app.helpers.normalize")
        normalize_mod.normalize_amount = lambda x: x
        plaid_mod = types.ModuleType("app.helpers.plaid_helpers")
        plaid_mod.get_accounts = lambda *a, **k: []
        plaid_mod.get_transactions = lambda *a, **k: []
        helpers_pkg.normalize = normalize_mod
        helpers_pkg.plaid_helpers = plaid_mod
        sys.modules["app.helpers"] = helpers_pkg
        sys.modules["app.helpers.normalize"] = normalize_mod
        sys.modules["app.helpers.plaid_helpers"] = plaid_mod
        sys.modules["app.sql.transaction_rules_logic"] = types.ModuleType(
            "app.sql.transaction_rules_logic"
        )
        refresh_mod = types.ModuleType("app.sql.refresh_metadata")
        refresh_mod.refresh_or_insert_plaid_metadata = lambda *a, **k: None
        sys.modules["app.sql.refresh_metadata"] = refresh_mod
        logic = load_module(
            "app.sql.account_logic",
            os.path.join(BASE_BACKEND, "app", "sql", "account_logic.py"),
        )
        extensions.db.create_all()
        yield extensions.db, models, logic
        extensions.db.drop_all()


def test_save_plaid_item_inserts_and_updates(db_ctx):
    db, models, logic = db_ctx

    # Insert
    item = logic.save_plaid_item(
        user_id="u1",
        item_id="item123",
        access_token="tok1",
        institution_name="InvestCo",
        product="investments",
    )
    assert item.id
    assert db.session.query(models.PlaidItem).count() == 1

    # Update
    item2 = logic.save_plaid_item(
        user_id="u1",
        item_id="item123",
        access_token="tok2",
        institution_name="InvestCo",
        product="investments",
    )
    assert item2.id == item.id
    assert item2.access_token == "tok2"
    assert db.session.query(models.PlaidItem).count() == 1
