"""Database bridge for recurring transaction detection.

This module links recurring transaction patterns detected in raw
transactions with database persistence utilities. Imports are deferred
until synchronization to avoid loading heavy dependencies at import time.
"""

from datetime import timedelta
from importlib import import_module

from app.services.recurring_detection import RecurringDetector
from app.sql import recurring_logic
from dateutil.parser import parse


class RecurringBridge:
    """Bridge recurring detection results to database persistence."""

    def __init__(self, transactions):
        """Initialize with raw transaction dictionaries."""
        self.transactions = transactions
        self.detector = RecurringDetector(transactions)

    def sync_to_db(self):
        """Detect recurring patterns and upsert them into the database."""
        # Import DB session and models only when syncing to avoid heavy
        # dependencies during module import. This also ensures models are
        # registered with the SQLAlchemy instance used by tests.
        _ = import_module("app.extensions")
        _ = import_module("app.models")

        candidates = self.detector.detect()
        actions = []

        freq_map = {
            "daily": 1,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
        }

        for item in candidates:
            if not item.get("account_id"):
                for tx in self.transactions:
                    desc_sig = "".join(filter(str.isalnum, tx["description"].lower()))[
                        :16
                    ]
                    if (
                        round(tx["amount"], 2) == item["amount"]
                        and desc_sig == item["description"]
                    ):
                        item["account_id"] = tx.get("account_id")
                        break

            last_seen = parse(item.get("last_seen")).date()
            freq_days = freq_map.get(item["frequency"].lower(), 30)
            next_due_date = last_seen + timedelta(days=freq_days)
            confidence = float(item.get("occurrences", 1)) / 10.0

            rec_id = recurring_logic.upsert_recurring(
                item["description"],
                item["amount"],
                item["frequency"],
                next_due_date,
                confidence,
                item.get("account_id"),
            )
            actions.append(rec_id)

        return actions
