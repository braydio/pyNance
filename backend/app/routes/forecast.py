from flask import Blueprint, jsonify, request
from app.models import Account, RecurringTransaction
from app.extensions import db
from app.services.forecast_balance import ForecastSimulator

forecast = Blueprint("forecast", __name__, url_prefix="/api/forecast")


@forecast.route("/balance", methods=["GET"])
def get_balance_projection():
    try:
        days = int(request.args.get("days", 30))

        account = db.session.query(Account).first()
        starting_balance = account.balance if account else 0.0

        recs = db.session.query(RecurringTransaction).all()
        recurring_events = [
            {
                "amount": r.transaction.amount,
                "frequency": r.frequency,
                "next_due_date": r.next_due_date.isoformat(),
            }
            for r in recs
        ]

        simulator = ForecastSimulator(starting_balance, recurring_events)
        forecast_data = simulator.project(days=days)

        return jsonify(forecast_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
