import os
import sys
import importlib.util
import types

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def setup_sqlite_app(tmp_path):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/test.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    extensions = load_module(
        "app.extensions", os.path.join(BASE_BACKEND, "app", "extensions.py")
    )
    extensions.db.init_app(app)
    return app, extensions


@pytest.fixture
def db_ctx(tmp_path):
    app, extensions = setup_sqlite_app(tmp_path)
    with app.app_context():
        sys.modules["app"] = types.ModuleType("app")
        sys.modules["app.extensions"] = extensions
        models = load_module(
            "app.models", os.path.join(BASE_BACKEND, "app", "models.py")
        )
        sys.modules["app.models"] = models
        sql_pkg = types.ModuleType("app.sql")
        sys.modules["app.sql"] = sql_pkg
        logic = load_module(
            "app.sql.recurring_logic",
            os.path.join(BASE_BACKEND, "app", "sql", "recurring_logic.py"),
        )
        sys.modules["app.sql.recurring_logic"] = logic
        extensions.db.create_all()
        yield extensions.db, models, logic
        extensions.db.drop_all()
        for mod in [
            "app.sql.recurring_logic",
            "app.sql",
            "app.models",
            "app.extensions",
            "app",
        ]:
            sys.modules.pop(mod, None)


def test_sync_to_db_inserts_recurring(db_ctx):
    db, models, _ = db_ctx
    services_pkg = types.ModuleType("app.services")
    sys.modules["app.services"] = services_pkg
    rec_det = load_module(
        "app.services.recurring_detection",
        os.path.join(BASE_BACKEND, "app", "services", "recurring_detection.py"),
    )
    sys.modules["app.services.recurring_detection"] = rec_det
    bridge = load_module(
        "app.services.recurring_bridge",
        os.path.join(BASE_BACKEND, "app", "services", "recurring_bridge.py"),
    )

    txs = [
        {
            "amount": 9.99,
            "description": "Netflix",
            "date": "2024-01-01",
            "account_id": "acc1",
        },
        {
            "amount": 9.99,
            "description": "Netflix",
            "date": "2024-02-01",
            "account_id": "acc1",
        },
        {
            "amount": 9.99,
            "description": "Netflix",
            "date": "2024-03-01",
            "account_id": "acc1",
        },
    ]

    rb = bridge.RecurringBridge(txs)
    results = rb.sync_to_db()
    assert len(results) == 1
    assert models.RecurringTransaction.query.count() == 1
    rec = models.RecurringTransaction.query.first()
    assert rec.id == results[0]
    assert rec.frequency
    assert rec.transaction.amount == 9.99


def test_sync_to_db_no_candidates(db_ctx):
    """Verify no DB rows are created when detection finds no recurring items."""
    db, models, _ = db_ctx
    services_pkg = types.ModuleType("app.services")
    sys.modules["app.services"] = services_pkg
    rec_det = load_module(
        "app.services.recurring_detection",
        os.path.join(BASE_BACKEND, "app", "services", "recurring_detection.py"),
    )
    sys.modules["app.services.recurring_detection"] = rec_det
    bridge = load_module(
        "app.services.recurring_bridge",
        os.path.join(BASE_BACKEND, "app", "services", "recurring_bridge.py"),
    )

    txs = [
        {"amount": 5.0, "description": "One-off", "date": "2024-01-01", "account_id": "acc1"},
        {"amount": 7.0, "description": "Another", "date": "2024-02-01", "account_id": "acc1"},
    ]

    rb = bridge.RecurringBridge(txs)
    results = rb.sync_to_db()
    assert results == []
    assert models.RecurringTransaction.query.count() == 0
