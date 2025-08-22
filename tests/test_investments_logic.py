import importlib.util
import os
import sys
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
    config_stub.FILES = {}
    sys.modules["app.config"] = config_stub

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
            "app.models",
            os.path.join(BASE_BACKEND, "app", "models", "__init__.py"),
        )
        logic = load_module(
            "app.sql.investments_logic",
            os.path.join(BASE_BACKEND, "app", "sql", "investments_logic.py"),
        )
        extensions.db.create_all()
        yield extensions.db, models, logic
        extensions.db.drop_all()


def test_get_investment_accounts(db_ctx):
    db, models, logic = db_ctx

    acc = models.Account(
        account_id="acct1",
        user_id="u1",
        name="Invest",
        type="brokerage",
    )
    db.session.add(acc)
    db.session.commit()
    pa = models.PlaidAccount(
        account_id="acct1",
        access_token="tok",
        item_id="it1",
        product="investments",
    )
    db.session.add(pa)
    db.session.commit()

    accounts = logic.get_investment_accounts()
    assert len(accounts) == 1
    assert accounts[0]["account_id"] == "acct1"
