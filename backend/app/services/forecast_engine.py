from datetime import datetime, timedelta
from app.models import RecurringTransaction
from sqlmalchemy.orm import Session

```python
class ForecastEngine:
    def __init__(self, db: Session):
        self.db = db
    def _expand_recurring(self, rt: RecurringTransaction, days_ahead=60):
        forecast_items = []
        freq = rt.frequency.lower()
        start = rt.next_due_date or datetime.utcnow()
        freq_map = {
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
            "semimonthly": 15,
            "yearly": 365
        }
        step = freq_map.get(freq)
        if not step:
            return []
        for i in range(0, days_ahead, step):
            next_date = start + timedelta(days=i)
            forecast_items.append({
                "date": next_date,
                "value": rt.transaction.amount,
                "description": rt.transaction.description,
                "account_id": rt.transaction.account_id,
                "type": "recurring",
                "frequency": freq
            })
        return forecast_items
    def forecast(self, days_ahead=60):
        results = []
        recurring = self.db.query(RecurringTransaction).all()
        for rt in recurring:
            projected = self._expand_recurring(rt, days_ahead)
            results.extend(projected)
        return sorted(results, key=lambda x: x["date"])