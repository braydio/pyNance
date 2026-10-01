"""Transactional, immutable Plaid source observations and ingestion coordination."""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select, text

from app.extensions import db
from app.models import PlaidSourceEvent, RecurringTransaction, Transaction
from app.sql.dialect_utils import dialect_insert
from app.sql.refresh_metadata import _sanitize_for_json

_context = ContextVar("plaid_source_context", default=None)
_SECRET_KEYS = {"access_token", "public_token", "secret", "client_id", "authorization", "password"}


def _source_json(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _source_json(v) for k, v in value.items() if str(k).lower() not in _SECRET_KEYS}
    if isinstance(value, (list, tuple)):
        return [_source_json(v) for v in value]
    return _sanitize_for_json(value)


@contextmanager
def source_context(**values):
    """Attach a run/page checkpoint without passing secrets through logging."""
    parent = _context.get() or {}
    token = _context.set({"run_id": parent.get("run_id") or str(uuid4()), **parent, **values})
    try:
        yield
    finally:
        _context.reset(token)


def ingestion_lock(key: str):
    """Serialize provider writers until commit/rollback (also covers legacy imports)."""
    if db.session.get_bind().dialect.name == "postgresql":
        db.session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})


def record_source(payload: dict, *, event_type="observed", account_id=None, item_id=None, endpoint=None):
    """Append a replay-safe original source payload; never commit independently."""
    context = _context.get() or {}
    transaction_id = payload.get("transaction_id")
    if not transaction_id:
        raise ValueError("Plaid source transaction_id is required")
    sanitized = _source_json(payload)
    encoded = json.dumps(sanitized, sort_keys=True, separators=(",", ":"), allow_nan=False)
    values = dict(
        run_id=context.get("run_id") or str(uuid4()),
        page_index=context.get("page_index", 0),
        event_type=context.get("event_type", event_type) if event_type == "observed" else event_type,
        transaction_id=transaction_id,
        account_id=account_id or payload.get("account_id"),
        item_id=item_id or context.get("item_id"),
        endpoint=endpoint or context.get("endpoint", "transactions/get"),
        request_id=context.get("request_id"),
        fetched_at=datetime.now(timezone.utc),
        payload=sanitized,
        payload_sha256=hashlib.sha256(encoded.encode()).hexdigest(),
        cursor_before=context.get("cursor_before"),
        cursor_after=context.get("cursor_after"),
    )
    stmt = dialect_insert(PlaidSourceEvent.__table__).values(**values)
    db.session.execute(
        stmt.on_conflict_do_nothing(index_elements=["run_id", "page_index", "event_type", "transaction_id"])
    )
    stored_hash = db.session.execute(
        select(PlaidSourceEvent.payload_sha256).filter_by(
            run_id=values["run_id"],
            page_index=values["page_index"],
            event_type=values["event_type"],
            transaction_id=transaction_id,
        )
    ).scalar_one()
    if stored_hash != values["payload_sha256"]:
        raise ValueError("Conflicting source payloads share the same Plaid event identity")


def modified_fields(transaction) -> set[str]:
    """Unknown legacy edit flags protect all provider-editable fields."""
    if not transaction.user_modified:
        return set()
    try:
        fields = json.loads(transaction.user_modified_fields or "null")
    except (TypeError, ValueError):
        fields = None
    if isinstance(fields, dict):
        return {key for key, enabled in fields.items() if enabled}
    if isinstance(fields, list):
        return set(fields)
    return {"amount", "date", "description", "category", "merchant_name", "merchant_type", "is_internal"}


def clear_transfer(transaction):
    """Unlink both ends before provider changes invalidate an automatic match."""
    if transaction.internal_match_id:
        other = Transaction.query.filter_by(transaction_id=transaction.internal_match_id).first()
        if other and other.internal_match_id == transaction.transaction_id:
            other.internal_match_id = None
            if "is_internal" not in modified_fields(other):
                other.is_internal = False
                other.transfer_type = None
    transaction.internal_match_id = None
    if "is_internal" not in modified_fields(transaction):
        transaction.is_internal = False
        transaction.transfer_type = None


def retire_transaction(transaction, *, reason, successor=None):
    """Preserve evidence and annotations before retiring an active provider row."""
    if successor and (transaction.account_id != successor.account_id or not transaction.pending):
        raise ValueError("Pending predecessor must be pending on the same account")
    record_source(
        {
            "transaction_id": transaction.transaction_id,
            "account_id": transaction.account_id,
            "reason": reason,
            "successor_id": successor.transaction_id if successor else None,
            "source": transaction.plaid_meta.raw if transaction.plaid_meta else None,
            "local": {column.name: getattr(transaction, column.name) for column in Transaction.__table__.columns},
            "tags": [{"id": tag.id, "name": tag.name, "user_id": tag.user_id} for tag in transaction.tags],
            "recurrences": [
                {column.name: getattr(rule, column.name) for column in RecurringTransaction.__table__.columns}
                for rule in RecurringTransaction.query.filter_by(transaction_id=transaction.transaction_id).all()
            ],
        },
        event_type="retired",
        endpoint="local/reconciliation",
    )
    if successor:
        for tag in transaction.tags:
            if tag not in successor.tags:
                successor.tags.append(tag)
        inherited = modified_fields(transaction)
        current = modified_fields(successor)
        # Category and merchant changes are persisted as coherent groups.
        groups = {
            "category": {"category_id", "category", "category_slug", "category_display"},
            "merchant_name": {"merchant_name", "merchant_slug"},
            "is_internal": {"is_internal", "transfer_type"},
        }
        for field in inherited:
            if field not in current:
                for attr in groups.get(field, {field}):
                    if hasattr(successor, attr):
                        setattr(successor, attr, getattr(transaction, attr))
        if inherited:
            successor.user_modified = True
            successor.user_modified_fields = json.dumps(dict.fromkeys(current | inherited, True))
        RecurringTransaction.query.filter_by(transaction_id=transaction.transaction_id).update(
            {"transaction_id": successor.transaction_id}, synchronize_session="fetch"
        )
    # next_instance_id is a logical reference rather than an FK.
    RecurringTransaction.query.filter_by(next_instance_id=transaction.transaction_id).update(
        {"next_instance_id": successor.transaction_id if successor else None}, synchronize_session="fetch"
    )
    clear_transfer(transaction)
    db.session.delete(transaction)
    db.session.flush()
