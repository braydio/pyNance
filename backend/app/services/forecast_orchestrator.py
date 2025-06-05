# forecast_orchestrator.py
from datetime import datetime, timedelta
from sqlalchemy import func
from .forecast_engine import ForecastEngine as ForecastEngineRuleBased
from .forecast_stat_model import ForecastEngine as ForecastEngineStatModel
from app.models import RecurringTransaction, Transaction, AccountHistory, Account
from app.sql.forecast_logic import generate_forecast_line


class ForecastOrchestrator:
    def __init__(self, db):
        self.db = db
        self.rule_engine = ForecastEngineRuleBased(db)
        self.stat_engine = ForecastEngineStatModel()

    def forecast(self, method="rule", days=60, stat_input=None):
        if method == "rule":
            return self.rule_engine.forecast_balances(horizon_days=days)
        elif method == "stat":
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

        start = datetime.utcnow().date()
        horizon = 30 if view_type.lower() == "month" else 365
        end = start + timedelta(days=horizon - 1)

        recs = (
            self.db.session.query(RecurringTransaction)
            .join(
                Transaction,
                RecurringTransaction.transaction_id == Transaction.transaction_id,
            )
            .join(Account, Transaction.account_id == Account.account_id)
            .filter(Transaction.user_id == user_id)
            .filter(Account.is_hidden.is_(False))
            .all()
        )

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
                }
            )

        labels, forecast_line = generate_forecast_line(
            start, end, items, manual_income, liability_rate
        )

        data = (
            self.db.session.query(
                func.date(AccountHistory.date), func.sum(AccountHistory.balance)
            )
            .filter(AccountHistory.user_id == user_id)
            .filter(AccountHistory.date >= start, AccountHistory.date <= end)
            .group_by(func.date(AccountHistory.date))
            .all()
        )
        lookup = {d[0]: float(d[1]) for d in data}
        actual_line = []
        current = start
        while current <= end:
            actual_line.append(lookup.get(current, None))
            current += timedelta(days=1)

        latest = (
            self.db.session.query(func.max(AccountHistory.date))
            .filter(AccountHistory.user_id == user_id)
            .scalar()
        )
        data_age = (start - latest.date()).days if latest else None

        metadata = {
            "account_count": self.db.session.query(Account)
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
