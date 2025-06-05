from flask import Blueprint, jsonify, request
from collections import defaultdict
from datetime import datetime, timedelta
from app.extensions import db
from app.services.forecast_orchestrator import ForecastOrchestrator
from app.models import AccountHistory

forecast = Blueprint("forecast", __name__)


@forecast.route("", methods=["GET"])
def get_forecast():
    try:
        view_type = request.args.get("view_type", "Month")
        horizon = 30 if view_type.lower() == "month" else 365

        orchestrator = ForecastOrchestrator(db.session)
        projections = orchestrator.forecast(days=horizon)

        daily_totals = defaultdict(float)
        for p in projections:
            day = p["date"].strftime("%Y-%m-%d") if hasattr(p["date"], "strftime") else str(p["date"])
            daily_totals[day] += p.get("balance", 0)

        labels = []
        forecast_line = []
        start = datetime.utcnow().date()
        for i in range(horizon):
            day = start + timedelta(days=i)
            labels.append(day.strftime("%b %d"))
            forecast_line.append(round(daily_totals.get(day.strftime("%Y-%m-%d"), 0), 2))

        actuals_map = defaultdict(float)
        history_rows = (
            db.session.query(AccountHistory)
            .filter(AccountHistory.date >= start)
            .filter(AccountHistory.date <= start + timedelta(days=horizon - 1))
            .all()
        )
        for row in history_rows:
            key = row.date.date()
            actuals_map[key] += row.balance

        actuals = [actuals_map.get(start + timedelta(days=i)) for i in range(horizon)]

        metadata = {
            "account_count": len({p["account_id"] for p in projections}),
            "recurring_count": 0,
            "data_age_days": 0,
        }

        return (
            jsonify(
                {
                    "labels": labels,
                    "forecast": forecast_line,
                    "actuals": actuals,
                    "metadata": metadata,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
