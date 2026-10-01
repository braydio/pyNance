"""PostgreSQL-only migrations, concurrency and append-only enforcement."""

import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from app.extensions import db
from app.models import Account, PlaidAccount, PlaidSourceEvent, PlaidTransactionMeta, Transaction
from app.services.plaid_audit import source_context
from app.services.plaid_sync import _upsert_transaction
from flask import Flask
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.integration


@pytest.fixture()
def postgres_app():
    uri = os.environ.get("PYNANCE_TEST_DATABASE_URI")
    if not uri:
        pytest.skip("Set PYNANCE_TEST_DATABASE_URI to an isolated PostgreSQL instance")
    schema = "test_plaid_" + uuid4().hex
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"options": f"-c search_path={schema}"}},
    )
    db.init_app(app)
    with app.app_context():
        with db.engine.begin() as c:
            c.execute(text("CREATE SCHEMA " + schema))
        db.create_all()
        # Reconstruct the two changed surfaces at the previous revision and
        # execute the actual Alembic upgrade, not an alternative test DDL.
        with db.engine.begin() as c:
            c.execute(text("DROP TABLE plaid_source_events"))
            c.execute(
                text(
                    "ALTER TABLE categories ADD CONSTRAINT uq_category_composite UNIQUE(primary_category,detailed_category)"
                )
            )
            path = Path("backend/migrations/versions/e6a9c2f4b8d1_plaid_source_audit_and_category_identity.py")
            spec = importlib.util.spec_from_file_location("plaid_audit_test_migration", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with Operations.context(MigrationContext.configure(c)):
                module.upgrade()
        db.session.add_all(
            [
                Account(account_id="checking", user_id="owner", name="Checking"),
                PlaidAccount(account_id="checking", item_id="item", access_token="x", product="transactions"),
            ]
        )
        db.session.commit()
    try:
        yield app
    finally:
        with app.app_context():
            db.session.remove()
            with db.engine.begin() as c:
                c.execute(text("DROP SCHEMA " + schema + " CASCADE"))
            db.engine.dispose()


def source():
    return {
        "transaction_id": "concurrent",
        "account_id": "checking",
        "date": "2026-09-01",
        "amount": 10,
        "name": "Apple",
        "pending": False,
        "personal_finance_category": {"primary": "GENERAL_MERCHANDISE", "detailed": "GENERAL_MERCHANDISE_ELECTRONICS"},
    }


def test_concurrent_identity_upsert_is_conflict_safe(postgres_app):
    barrier = Barrier(2)

    def writer():
        with postgres_app.app_context():
            barrier.wait(timeout=5)
            with source_context(run_id="same-request"):
                account = db.session.get(Account, "checking")
                linked = PlaidAccount.query.one()
                _upsert_transaction(source(), account, linked)
                db.session.commit()
            db.session.remove()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(writer) for _ in range(2)]
        for f in futures:
            f.result(timeout=15)
    with postgres_app.app_context():
        assert Transaction.query.count() == 1
        assert PlaidTransactionMeta.query.count() == 1
        assert PlaidSourceEvent.query.count() == 1


def test_source_events_reject_update_delete_and_truncate(postgres_app):
    with postgres_app.app_context():
        _upsert_transaction(source(), db.session.get(Account, "checking"), PlaidAccount.query.one())
        db.session.commit()
        for statement in [
            "UPDATE plaid_source_events SET endpoint='tampered'",
            "DELETE FROM plaid_source_events",
            "TRUNCATE plaid_source_events",
        ]:
            with pytest.raises(DBAPIError, match="append-only"):
                with db.session.begin_nested():
                    db.session.execute(text(statement))
        assert PlaidSourceEvent.query.count() == 1
