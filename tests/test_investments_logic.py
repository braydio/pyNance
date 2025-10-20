"""Tests for investment account logic."""

# pylint: skip-file
# mypy: ignore-errors

import importlib.util
import os
import sys
import types
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

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
    config_stub.DIRECTORIES = {
        "CERTS_DIR": Path(tmp_path),
        "DATA_DIR": Path(tmp_path),
    }
    sys.modules["app.config"] = config_stub

    extensions = load_module(
        "app.extensions", os.path.join(BASE_BACKEND, "app", "extensions.py")
    )
    extensions.db.init_app(app)
    return app, extensions


@pytest.fixture(scope="module")
def app_modules(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("investments_logic")
    app, extensions = setup_app(tmp_dir)
    models = load_module(
        "app.models",
        os.path.join(BASE_BACKEND, "app", "models", "__init__.py"),
    )
    logic = load_module(
        "app.sql.investments_logic",
        os.path.join(BASE_BACKEND, "app", "sql", "investments_logic.py"),
    )
    return app, extensions, models, logic


@pytest.fixture()
def db_ctx(app_modules):
    app, extensions, models, logic = app_modules
    with app.app_context():
        extensions.db.drop_all()
        extensions.db.create_all()
        yield extensions.db, models, logic
        extensions.db.session.remove()


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


def test_upsert_investment_transactions_persists_json(db_ctx):
    db, models, logic = db_ctx

    payload = {
        "investment_transaction_id": "tx-raw",
        "account_id": "acct-raw",
        "security_id": "sec-raw",
        "date": date(2024, 1, 1),
        "amount": Decimal("10.50"),
        "price": Decimal("1.05"),
        "quantity": Decimal("10"),
        "subtype": "buy",
        "type": "buy",
        "name": "Sample",
        "fees": Decimal("0.10"),
        "iso_currency_code": "USD",
        "nested": {
            "posted_at": datetime(2024, 1, 1, 12, 30),
            "legs": [Decimal("5.25"), {"when": date(2024, 1, 2)}],
        },
    }

    processed = logic.upsert_investment_transactions([payload])

    assert processed == 1
    stored = db.session.get(models.InvestmentTransaction, "tx-raw")
    assert stored is not None
    assert stored.raw["amount"] == pytest.approx(10.5)
    assert stored.raw["nested"]["posted_at"] == datetime(2024, 1, 1, 12, 30).isoformat()
    assert stored.raw["nested"]["legs"][0] == pytest.approx(5.25)
    assert stored.raw["nested"]["legs"][1]["when"] == date(2024, 1, 2).isoformat()
