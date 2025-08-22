# tests/test_recurring_bridge.py
import importlib.util
import logging
import os
import sys
import types

import pytest
from flask import Flask

# Configure logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_runner")

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)


def load_module(name, path):
    try:
        if path.endswith("__init__.py"):
            spec = importlib.util.spec_from_file_location(
                name, path, submodule_search_locations=[os.path.dirname(path)]
            )
        else:
            spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        logger.debug(f"Loaded module: {name} from {path}")
        return module
    except Exception as e:
        logger.exception(f"Failed to load module '{name}' at '{path}' error: {e}")
        raise


def setup_sqlite_app(tmp_path):
    try:
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/test.db"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        extensions = load_module(
            "app.extensions", os.path.join(BASE_BACKEND, "app", "extensions.py")
        )
        extensions.db.init_app(app)
        return app, extensions
    except Exception as e:
        logger.exception(f"Failed to set up SQLite Flask app causing error: {e}")
        raise


@pytest.fixture
def db_ctx(tmp_path):
    app, extensions = setup_sqlite_app(tmp_path)
    with app.app_context():
        try:
            sys.modules["app"] = types.ModuleType("app")
            sys.modules["app.extensions"] = extensions

            models = load_module(
                "app.models",
                os.path.join(BASE_BACKEND, "app", "models", "__init__.py"),
            )

            sys.modules["app.sql"] = types.ModuleType("app.sql")
            logic = load_module(
                "app.sql.recurring_logic",
                os.path.join(BASE_BACKEND, "app", "sql", "recurring_logic.py"),
            )
            sys.modules["app.sql.recurring_logic"] = logic

            extensions.db.create_all()
            yield extensions.db, models, logic

        except Exception as e:
            logger.exception(f"Fixture setup causing error: {e}")
            raise
        finally:
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
    try:
        # Load service modules
        sys.modules["app.services"] = types.ModuleType("app.services")

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

        logger.debug("Instantiating RecurringBridge with transactions")
        rb = bridge.RecurringBridge(txs)
        results = rb.sync_to_db()

        logger.debug("Asserting sync results")
        assert len(results) == 1, "Expected 1 recurring transaction inserted"
        assert models.RecurringTransaction.query.count() == 1

        rec = models.RecurringTransaction.query.first()
        assert rec.id == results[0]
        assert rec.frequency, "Expected frequency to be inferred"
        assert rec.transaction.amount == 9.99

    except AssertionError as ae:
        logger.error(f"Assertion failed: {ae}")
        raise

    except Exception as e:
        logger.exception(f"Unexpected error during recurring sync test {e}")
        raise
