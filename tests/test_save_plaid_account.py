import importlib.util
import os

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
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
