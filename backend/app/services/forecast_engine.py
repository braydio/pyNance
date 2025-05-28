
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.models import RecurringTransaction, AccountHistory


class ForecastEngine:
    def __init__(self, db: Session):
        self.db = db

    def _generate_projection_dates(self, start: datetime, freq: str, horizon: int) -> List[datetime]:
        delta_map = {
            "daily": 1,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
        }
        interval = delta_map.get(freq.lower(), 30)
        dates = []
        current = start
        end = start + timedelta(days=horizon)

        while current <= end:
            dates.append(current)
            current += timedelta(days=interval)
        return dates

    def forecast(self, horizon_days: int = 60):
        forecast = []

        recurrences = self.db.query(RecurringTransaction).all()
        today = datetime.utcnow()

        for r in recurrences:
            if not r.next_due_date or not r.frequency:
                continue

            dates = self._generate_projection_dates(
                start=r.next_due_date,
                freq=r.frequency,
                horizon=horizon_days
            )

            for d in dates:
                forecast.append({
                    "date": d,
                    "account_id": r.transaction.account_id if r.transaction else None,
                    "amount": r.transaction.amount if r.transaction else 0,
                    "description": r.transaction.description if r.transaction else "Recurring",
                    "type": "recurring",
                    "frequency": r.frequency
                })

        return forecast
