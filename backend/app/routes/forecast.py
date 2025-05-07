from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import Account, AccountHistory, RecurringTransaction
import logging

forecast = Blueprint("forecast", __name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@forecast.route("/api/forecast/summary", methods=["GET"])
def forecast_summary():
    """
    Returns forecast and actual account balances over a specified time range.
    Query Parameters:
        - user_id: ID of the user
        - viewType: 'Month' or 'Year'
        - manualIncome: Optional manual income override
        - liabilityRate: Optional liability rate override
    """
    user_id = request.args.get("user_id")
    view_type = request.args.get("viewType", "Month")
    manual_income = request.args.get("manualIncome", type=float)
    liability_rate = request.args.get("liabilityRate", type=float)

    # Validate user_id
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Determine date range based on viewType
    today = datetime.utcnow().date()
    if view_type == "Year":
        end_date = today + timedelta(days=365)
    else:  # Default to 'Month'
        end_date = today + timedelta(days=30)

    # Generate date labels
    date_labels = []
    current_date = today
    while current_date <= end_date:
        date_labels.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    # Fetch recurring transactions for the user
    recurring_txs = (
        RecurringTransaction.query.join(Account)
        .filter(Account.user_id == user_id)
        .all()
    )

    # Initialize forecast dictionary
    forecast_dict = {label: 0.0 for label in date_labels}

    # Apply recurring transactions to forecast
    for tx in recurring_txs:
        # Determine the next due date
        next_due_date = tx.next_due_date
        if not next_due_date or next_due_date > end_date:
            continue

        # Apply transaction amount to forecast dates
        current_tx_date = next_due_date
        while current_tx_date <= end_date:
            label = current_tx_date.strftime("%Y-%m-%d")
            if label in forecast_dict:
                forecast_dict[label] += tx.amount
            # Determine next occurrence based on frequency
            if tx.frequency == "monthly":
                current_tx_date += timedelta(days=30)
            elif tx.frequency == "weekly":
                current_tx_date += timedelta(weeks=1)
            elif tx.frequency == "daily":
                current_tx_date += timedelta(days=1)
            else:
                break  # Unsupported frequency

    # Apply manual income override if provided
    if manual_income:
        for label in forecast_dict:
            forecast_dict[label] += manual_income

    # Apply liability rate override if provided
    if liability_rate:
        for label in forecast_dict:
            forecast_dict[label] -= liability_rate

    # Fetch actual account history for the user
    account_histories = (
        AccountHistory.query.join(Account)
        .filter(
            Account.user_id == user_id,
            AccountHistory.date >= today,
            AccountHistory.date <= end_date,
        )
        .all()
    )

    # Initialize actuals dictionary
    actuals_dict = {label: None for label in date_labels}

    # Populate actuals with account history data
    for history in account_histories:
        label = history.date.strftime("%Y-%m-%d")
        if label in actuals_dict:
            if actuals_dict[label] is None:
                actuals_dict[label] = 0.0
            actuals_dict[label] += history.balance

    # Prepare response data
    forecast_values = [forecast_dict[label] for label in date_labels]
    actuals_values = [actuals_dict[label] for label in date_labels]

    response = {
        "labels": date_labels,
        "forecast": forecast_values,
        "actuals": actuals_values,
        "metadata": {
            "account_count": Account.query.filter_by(user_id=user_id).count(),
            "total_income_sources": len(recurring_txs),
            "discrepancy": sum(
                (f - a)
                for f, a in zip(forecast_values, actuals_values)
                if a is not None
            ),
        },
    }

    return jsonify(response)
