from flask import Blueprint, jsonify, request
from app.services.forecast_balance import ForecastSimulator
from app.extensions import db
from app.models import Account, RecurringTransaction, Transaction
from datetime import datetime

forecast = Blueprint("forecast", __name__)


@forecast.route("/forecast", methods=["GET"])
def get_forecast():
    try:
        days = int(request.args.get("days", 30))
        if not 1 <= days <= 90:
            return jsonify({"error": "days must be between 1 and 90"}), 400

        primary_account = (
            Account.query.filter_by(is_primary=True)
            .filter(Account.is_hidden.is_(False))
            .first()
        )
        if not primary_account:
            return jsonify({"error": "Primary account not found"}), 404

        rec_events = []
        recs = (
            RecurringTransaction.query.join(Transaction)
            .join(Account, Transaction.account_id == Account.account_id)
            .filter(Account.is_hidden.is_(False))
            .all()
        )
        for r in recs:
            tx = r.transaction
            if not tx:
                continue
            rec_events.append(
                {
                    "amount": tx.amount,
                    "next_due_date": r.next_due_date.isoformat(),
                    "frequency": r.frequency,
                }
            )

        sim = ForecastSimulator(primary_account.current_balance, rec_events)
        result = sim.project(days=days)
        return jsonify({"status": "success", "data": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
