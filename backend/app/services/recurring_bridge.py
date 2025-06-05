from datetime import timedelta, datetime
from importlib import import_module

from dateutil.parser import parse
from app.services.recurring_detection import RecurringDetector
from app.sql import recurring_logic


class RecurringBridge:
    """
    Links RecurringDetector output to DB persistence via recurring_logic helpers.
    """

    def __init__(self, transactions):
        self.detector = RecurringDetector(transactions)

    def sync_to_db(self):
        """Detect recurring patterns and upsert them into the database."""
        # Import DB session and models only when syncing to avoid heavy
        # dependencies during module import. This also ensures models are
        # registered with the SQLAlchemy instance used by tests.
        import_module("app.extensions").db  # noqa: F401 - load session
        import_module("app.models")

        candidates = self.detector.detect()
        actions = []

        freq_map = {
            "daily": 1,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
        }

        for item in candidates:
            last_seen = parse(item.get("last_seen")).date()
            freq_days = freq_map.get(item["frequency"].lower(), 30)
            next_due = last_seen + timedelta(days=freq_days)
            confidence = float(item.get("occurrences", 1)) / 10.0

            result = recurring_logic.upsert_recurring(
                amount=item["amount"],
                description=item["description"],
                frequency=item["frequency"],
                next_due_date=next_due,
                confidence=confidence,
            )
            actions.append(result)

        return actions
