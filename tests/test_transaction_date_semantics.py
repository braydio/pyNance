"""Regression tests for calendar-date transaction persistence."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import Date, DateTime

BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
os.environ.setdefault("PLAID_CLIENT_ID", "sandbox-client")
os.environ.setdefault("PLAID_SECRET_KEY", "sandbox-secret")
os.environ.setdefault("CLIENT_NAME", "pyNance Test Suite")
os.environ.setdefault("BACKEND_PUBLIC_URL", "http://localhost")

for module_name in list(sys.modules):
    if not (
        module_name in {"app.config", "app.extensions", "app.models", "app.services", "app.sql", "app.utils"}
        or module_name.startswith(("app.config.", "app.models.", "app.services.", "app.sql.", "app.utils."))
    ):
        continue
    existing = sys.modules.get(module_name)
    if existing is not None and getattr(existing, "__file__", None) is None:
        sys.modules.pop(module_name, None)

app_module = sys.modules.get("app")
if app_module is not None and getattr(app_module, "__file__", None) is None:
    sys.modules.pop("app", None)

from app.models import PlaidTransactionMeta, Transaction  # noqa: E402


def test_transaction_date_is_date_while_plaid_timestamps_remain_datetimes():
    transaction_date_type = Transaction.__table__.c.date.type
    assert isinstance(transaction_date_type, Date)
    assert not isinstance(transaction_date_type, DateTime)
    assert isinstance(PlaidTransactionMeta.__table__.c.datetime.type, DateTime)
    assert PlaidTransactionMeta.__table__.c.datetime.type.timezone is True
    assert isinstance(PlaidTransactionMeta.__table__.c.authorized_datetime.type, DateTime)
    assert PlaidTransactionMeta.__table__.c.authorized_datetime.type.timezone is True


def test_migration_preserves_existing_utc_calendar_day():
    migration = (BASE_DIR / "backend/migrations/versions/7c1e9f4a2b6d_transactions_date_to_calendar_date.py").read_text(
        encoding="utf-8"
    )
    assert "(date AT TIME ZONE 'UTC')::date" in migration
    assert "date::timestamp AT TIME ZONE 'UTC'" in migration


def test_plaid_datetime_migration_uses_original_offset_values():
    migration = (
        BASE_DIR / "backend/migrations/versions/8d2f0a5b3c7e_plaid_metadata_datetimes_timezone_aware.py"
    ).read_text(encoding="utf-8")
    assert "(raw->>'datetime')::timestamptz" in migration
    assert "(raw->>'authorized_datetime')::timestamptz" in migration
