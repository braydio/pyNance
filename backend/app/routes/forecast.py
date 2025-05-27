# routes/forecast.py
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import db, Account, AccountHistory, RecurringTransaction, Transaction
import logging

forecast = Blueprint('forecast', __name__)
logger = logging.getLogger(__name__)

@forecast.route('/api/forecast/calculate', methods=['POST'])
def calculate_forecast():
    data = request.get_json()
    user_id = data.get('user_id')
    view_type = data.get('viewType', "Month")
    manual_income = float(data.get('manualIncome', 0.0))
    liability_rate = float(data.get('liabilityRate', 0.0))

    if not user_id:
        return jsonify({ "error": "user_id is required" }), 400

    today = datetime.utcnow().date()
    if view_type == "Year":
        end_date = today + timedelta(days=365)
    else:
        end_date = today + timedelta(days=30)

    date_labels = []
    current_date = today
    while current_date <= end_date:
        date_labels.append(current_date.strftime("%Y-%m-%d"))
        current_date = current_date + timedelta(days=1)

    # Fetch actual data from account_history
    ah_map = { r.get('date'): r.get('balance')
               for r in db.query(AccountHistory)
                         .filter(AccountHistory.user_id == user_id) }

    # Sum for transactions by date
    tx_map = { tx.date.strftime("%Y-%m-%d"): 
               sum(tx.amount for tx in db.query(Transaction)
                                       .filter(Transaction.user_id == user_id)) }

    # Calculate forecast, actual, delta
    forecast = []
    actuals = []
    delta = []

    for label in date_labels:
        f_value = manual_income - liability_rate       
        # Optional: derive from most recently synced account balance if ah_map is sparse
        a_value = ah_map.get(label) or sum([
            get_latest_balance_for_account(acct.account_id, user_id)
            for acct in Account.query.filter_by(user_id=user_id).all()
        ])

        d_value = round(f_value - a_value, 2)
        forecast.append(f_value)
        actuals.append(a_value)
        delta.append(d_value)

    return jsonify({
        "labels": date_labels,
        "forecast": forecast,
        "actuals": actuals,
        "metadata": {
            "account_count": Account.query.filter_by(user_id=user_id).count(),
            "total_income_sources": len(tx_map),
            "discrepancy": round(sum(forecast) - sum(actuals), 2)
        }
    })

