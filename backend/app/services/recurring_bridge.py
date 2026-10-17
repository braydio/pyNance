"""Compatibility bridge from detector results to recurring streams.

The old bridge guessed a 30-day cadence and wrote through a fabricated-transaction path. It now
runs the canonical detector and stores ``proposed`` streams through the owner-scoped repository.
It never creates a ``Transaction`` and never overwrites a confirmed, ignored or ended stream.
"""

from __future__ import annotations

from datetime import date
from importlib import import_module

from dateutil.parser import parse

from app.services.recurring_candidate_service import detect_candidate_streams


class RecurringBridge:
    """Bridge recurring detection results to database persistence."""

    def __init__(self, transactions):
        """Initialize with transaction dictionaries (``account_id`` is required to persist)."""
        self.transactions = transactions

    def sync_to_db(self):
        """Detect candidates and upsert them as proposed streams; returns the stream ids touched.

        Rows without an ``account_id`` cannot be scoped to an owner and are ignored.
        """
        # Imported lazily so merely importing this module does not need the full application.
        _ = import_module("app.extensions")
        models = import_module("app.models")
        repository = import_module("app.services.recurring_repository")

        scoped = [t for t in self.transactions if t.get("account_id")]
        if not scoped:
            return []
        owner_id = repository.trusted_owner_id()
        account_ids = sorted({str(t["account_id"]) for t in scoped})
        accounts = [
            {
                "account_id": a.account_id,
                "type": a.type,
                "subtype": a.subtype,
                "is_investment": a.is_investment,
                "user_id": a.user_id,
            }
            for a in models.Account.query.filter(
                models.Account.account_id.in_(account_ids), models.Account.user_id == owner_id
            ).all()
        ]
        rows = [
            {
                "transaction_id": str(t.get("transaction_id") or f"bridge-{i}"),
                "account_id": str(t["account_id"]),
                "date": parse(str(t["date"])).date(),
                "amount": t["amount"],
                "name": t.get("description"),
                "merchant_name": t.get("merchant_name"),
                "pending": bool(t.get("pending", False)),
                "is_internal": bool(t.get("is_internal", False)),
            }
            for i, t in enumerate(scoped)
        ]
        as_of = max(r["date"] for r in rows) if rows else date.today()
        found = detect_candidate_streams(rows, accounts, as_of, lookback_days=800)
        return [repository.upsert_detected_candidate(owner_id, c)[0].id for c in found["candidates"]]
