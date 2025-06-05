from flask import Blueprint, jsonify, request
from datetime import datetime
from app.extensions import db
from app.models import Account, RecurringTransaction, Transaction
from app.services.forecast_balance import ForecastSimulator
from app.services.forecast_orchestrator import ForecastOrchestrator

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


@forecast.route("", methods=["GET"])
def forecast_summary():
    """Return aggregated forecast and actual lines for a user."""
    try:
        user_id = request.args.get("user_id")
        view_type = request.args.get("view_type", "Month")
        manual_income = float(request.args.get("manual_income", 0.0))
        liability_rate = float(request.args.get("liability_rate", 0.0))

        orch = ForecastOrchestrator(db)
        payload = orch.build_forecast_payload(
            user_id=user_id,
            view_type=view_type,
            manual_income=manual_income,
            liability_rate=liability_rate,
        )
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@forecast.route("/calculate", methods=["POST"])
def forecast_calculate():
    """Calculate forecast using POSTed overrides."""
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id")
        view_type = data.get("view_type", "Month")
        manual_income = float(data.get("manual_income", 0.0))
        liability_rate = float(data.get("liability_rate", 0.0))

        orch = ForecastOrchestrator(db)
        payload = orch.build_forecast_payload(
            user_id=user_id,
            view_type=view_type,
            manual_income=manual_income,
            liability_rate=liability_rate,
        )
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
