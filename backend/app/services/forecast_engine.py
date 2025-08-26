# forecast_engine.py

"""Rule-based forecast engine for projecting account balances."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List

from app.models import AccountHistory, RecurringTransaction
from sqlalchemy.orm import Session


class ForecastEngine:
    """Generate recurring transaction forecasts and projected balances."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _generate_projection_dates(
        start: datetime, freq: str, horizon: int
    ) -> List[datetime]:
        """Build a list of projection dates using a frequency string."""
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
        """Return forecasted transaction events for the given horizon."""
        forecast = []
        recurrences = self.db.query(RecurringTransaction).all()

        for r in recurrences:
            if not r.next_due_date or not r.frequency:
                continue
            dates = self._generate_projection_dates(
                start=r.next_due_date, freq=r.frequency, horizon=horizon_days
            )
            for d in dates:
                forecast.append(
                    {
                        "date": d,
                        "account_id": (
                            r.transaction.account_id if r.transaction else None
                        ),
                        "amount": r.transaction.amount if r.transaction else 0,
                        "description": (
                            r.transaction.description if r.transaction else "Recurring"
                        ),
                        "type": "recurring",
                        "frequency": r.frequency,
                    }
                )
        return forecast

    def forecast_balances(self, horizon_days: int = 60):
        """Aggregate forecasted transactions into daily account balances."""
        forecast_txns = self.forecast(horizon_days=horizon_days)
        balances = {}

        latest_balances = (
            self.db.query(AccountHistory.account_id, AccountHistory.balance)
            .order_by(AccountHistory.account_id, AccountHistory.updated_at.desc())
            .distinct(AccountHistory.account_id)
            .all()
        )
        for acc_id, bal in latest_balances:
            balances[acc_id] = bal

        daily_txns = defaultdict(lambda: defaultdict(float))
        for txn in forecast_txns:
            daily_txns[txn["date"].date()][txn["account_id"]] += txn["amount"]

        output = []
        for i in range(horizon_days):
            day = (datetime.now(timezone.utc) + timedelta(days=i)).date()
            for acc_id in balances:
                delta = daily_txns[day][acc_id]
                balances[acc_id] += delta
                output.append(
                    {"date": day, "account_id": acc_id, "balance": balances[acc_id]}
                )
        return output
