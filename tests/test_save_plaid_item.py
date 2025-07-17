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
