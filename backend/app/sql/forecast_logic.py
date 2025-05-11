<<<<<<< HEAD

from datetime import datetime
from backend.app.models import AccountHistory, db

def get_latest_balance_for_account(account_id: str, user_id: str) => float:
    """
    Returns the most recent balance for the given account and user
    based on AccountHistory. Returns 0.0 if no entry is found.
    """
    latest = (
        db.session.query(AccountHistory)
        .filter_by(account_id=account_id, user_id=user_id)
        .order_by(AccountHistory.date.desc())
        .first()
    )
    return latest.balance if latest else 0.0
=======
# backend/app/sql/forecast_logic.py

from datetime import datetime, timedelta

def generate_forecast_line(start_date, end_date, recurring_items=None, manual_income=0.0, liability_rate=0.0):
    """
    Generate a forecasted daily balance line.
    """
    current_date = start_date
    forecast_line = []
    labels = []

    balance = 0.0
    recurring_items = recurring_items or []

    while current_date <= end_date:
        daily_income = manual_income / 30 if manual_income else 0.0
        daily_expense = liability_rate / 30 if liability_rate else 0.0

        for item in recurring_items:
            if item['frequency'] == 'monthly' and current_date.day == item['day']:
                balance += item['amount']
            # Add more recurrence types here as needed

        balance += daily_income - daily_expense
        forecast_line.append(round(balance, 2))
        labels.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    return labels, forecast_line

def calculate_deltas(forecast_line, actuals_line):
    return [
        round(f - a, 2) if a is not None else None
        for f, a in zip(forecast_line, actuals_line)
    ]

def update_account_history(account_id: str, user_id: str, balance: float, date: datetime = None):
    date = date or datetime.utcnow().date()
    exists = AccountHistory.query.filter_by(account_id=account_id, user_id=user_id, date=date).first()
    if not exists:
        db.session.add(AccountHistory(
            account_id=account_id,
            user_id=user_id,
            balance=balance,
            date=date
        ))
        db.session.commit()
>>>>>>> 4da7861 (2025-05-11 - forecast_logic.py - v1.0.0)
