# backend/app/sql/forecast_logic.py
from datetime import datetime, timedelta
from app.models import AccountHistory
from app.extensions import db
from app.config import logger
from sqlalchemy.dialects.sqlite import insert


def get_latest_balance_for_account(account_id: str, user_id: str) -> float:
    """
    Returns the most recent balance for the given account and user
    based on AccountHistory. Returns 0.0 if no entry is found.
    """

    if not user_id:
        raise ValueError("Cannot update account history without user_id")

    latest = (
        db.session.query(AccountHistory)
        .filter_by(account_id=account_id, user_id=user_id)
        .order_by(AccountHistory.date.desc())
        .first()
    )
    return latest.balance if latest else 0.0


def update_account_history(account_id, user_id, balance):
    today = datetime.utcnow().date()
    now = datetime.utcnow()

    try:
        stmt = (
            insert(AccountHistory)
            .values(
                account_id=account_id,
                user_id=user_id,
                date=today,
                balance=balance,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["account_id", "date"],
                set_={
                    "balance": balance,
                    "updated_at": now,
                },
            )
        )
        db.session.execute(stmt)
        db.session.commit()
        logger.debug(f"AccountHistory upserted for {account_id} on {today}")
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Failed to update AccountHistory for {account_id}: {e}", exc_info=True
        )


def generate_forecast_line(
    start_date, end_date, recurring_items=None, manual_income=0.0, liability_rate=0.0
):
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
            if item["frequency"] == "monthly" and current_date.day == item["day"]:
                balance += item["amount"]
            # Extend for weekly, biweekly, etc.

        balance += daily_income - daily_expense
        forecast_line.append(round(balance, 2))
        labels.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return labels, forecast_line


def calculate_deltas(forecast_line, actuals_line):
    """
    Calculate delta between forecast and actuals.
    """
    return [
        round(f - a, 2) if a is not None else None
        for f, a in zip(forecast_line, actuals_line)
    ]
