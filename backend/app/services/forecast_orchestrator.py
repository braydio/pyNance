# forecast_orchestrator.py
from datetime import datetime, timedelta, timezone

from app.models import Account, AccountHistory
from app.sql import forecast_logic
from sqlalchemy import func

from .forecast_engine import ForecastEngine as ForecastEngineRuleBased

try:  # Optional dependency
    from .forecast_stat_model import ForecastEngine as ForecastEngineStatModel
except Exception:  # pragma: no cover - allow missing heavy deps
    ForecastEngineStatModel = None


class ForecastOrchestrator:
    def __init__(self, db):
        self.db = db
        self.rule_engine = ForecastEngineRuleBased(db)
        self.stat_engine = (
            ForecastEngineStatModel() if ForecastEngineStatModel else None
        )

    def forecast(self, method="rule", days=60, stat_input=None):
        if days <= 0:
            raise ValueError("days must be positive")
        if method == "rule":
            return self.rule_engine.forecast_balances(horizon_days=days)
        elif method == "stat":
            if self.stat_engine is None:
                raise ImportError("Statistical forecast engine not available")
            if stat_input is None:
                raise ValueError(
                    "Statistical forecast requires a time series input (pd.Series)."
                )
            self.stat_engine.fit(stat_input)
            return self.stat_engine.forecast(steps=days)
        else:
            raise ValueError("Unknown forecast method: choose 'rule' or 'stat'")

    def build_forecast_payload(
        self, user_id, view_type="Month", manual_income=0.0, liability_rate=0.0
    ):
        """Assemble forecast and actual lines with metadata."""

        start = datetime.now(timezone.utc).date()
        horizon = 30 if view_type.lower() == "month" else 365
        end = start + timedelta(days=horizon - 1)

        recs = forecast_logic.list_recurring_transactions(user_id)

        items = []
        for r in recs:
            tx = r.transaction
            if not tx:
                continue
            items.append(
                {
                    "amount": tx.amount,
                    "frequency": r.frequency,
                    "day": r.next_due_date.day,
                    "start_date": r.next_due_date,
                }
            )

        labels, forecast_line = forecast_logic.generate_forecast_line(
            start, end, items, manual_income, liability_rate
        )

        lookup = forecast_logic.get_account_history_range(user_id, start, end)
        actual_line = []
        current = start
        while current <= end:
            actual_line.append(lookup.get(current, None))
            current += timedelta(days=1)

        latest = (
            self.db.query(func.max(AccountHistory.date))
            .filter(AccountHistory.user_id == user_id)
            .scalar()
        )
        data_age = (start - latest.date()).days if latest else None

        metadata = {
            "account_count": self.db.query(Account)
            .filter_by(user_id=user_id, is_hidden=False)
            .count(),
            "recurring_count": len(recs),
            "data_age_days": data_age or 0,
        }

        return {
            "labels": labels,
            "forecast": forecast_line,
            "actuals": actual_line,
            "metadata": metadata,
        }
