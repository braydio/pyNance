from flask import Blueprint, jsonify, request
from collections import defaultdict
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Account, RecurringTransaction, Transaction
from datetime import datetime

forecast = Blueprint("forecast", __name__)


@forecast.route("", methods=["GET"])
def get_forecast():
    try:
        view_type = request.args.get("view_type", "Month")
        horizon = 30 if view_type.lower() == "month" else 365

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
