from app.services.recurring_detection import RecurringDetector
from app.sql import recurring_logic

# TODO: Import db session and models when integrating


class RecurringBridge:
    """
    Links RecurringDetector output to DB persistence via recurring_logic helpers.
    """

    def __init__(self, transactions):
        self.detector = RecurringDetector(transactions)

    def sync_to_db(self):
        candidates = self.detector.detect()
        actions = []

        for item in candidates:
            # Use existing recurring_logic helper here to upsert
            result = recurring_logic.upsert_recurring(
                amount=item["amount"],
                description=item["description"],
                frequency=item["frequency"],
                next_due_date=item["next_due_date"],
                confidence=item["confidence"],
            )
            actions.append(result)

        return actions

