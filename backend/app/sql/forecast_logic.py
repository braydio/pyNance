# backend/app/sql/forecast_logic.py
from datetime import datetime, timedelta, timezone

from app.config import logger
from app.extensions import db
from app.models import Account, AccountHistory, RecurringTransaction, Transaction
from sqlalchemy import func
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


def update_account_history(account_id, user_id, balance, is_hidden=None):
    today = datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc)

    try:
        stmt = (
            insert(AccountHistory)
            .values(
                account_id=account_id,
                user_id=user_id,
                date=today,
                balance=balance,
                is_hidden=is_hidden,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["account_id", "date"],
                set_={
                    "balance": balance,
                    "updated_at": now,
                    "is_hidden": is_hidden,
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
            freq = item.get("frequency", "monthly").lower()
            start = item.get("start_date", start_date)

            if freq == "monthly" and current_date.day == item.get("day", 1):
                balance += item["amount"]
            elif freq == "weekly":
                if (current_date - start).days % 7 == 0 and (
                    current_date - start
                ).days >= 0:
                    balance += item["amount"]
            elif freq == "biweekly":
                if (current_date - start).days % 14 == 0 and (
                    current_date - start
                ).days >= 0:
                    balance += item["amount"]
            elif freq == "daily":
                balance += item["amount"]

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


def list_recurring_transactions(user_id):
    """Return active recurring transactions for the user."""
    return (
        db.session.query(RecurringTransaction)
        .join(
            Transaction,
            RecurringTransaction.transaction_id == Transaction.transaction_id,
        )
        .join(Account, Transaction.account_id == Account.account_id)
        .filter(Transaction.user_id == user_id)
        .filter(Account.is_hidden.is_(False))
        .all()
    )


def get_account_history_range(user_id, start_date, end_date):
    """Aggregate daily balances for the given range."""
    data = (
        db.session.query(
            func.date(AccountHistory.date), func.sum(AccountHistory.balance)
        )
        .filter(AccountHistory.user_id == user_id)
        .filter(AccountHistory.date >= start_date, AccountHistory.date <= end_date)
        .group_by(func.date(AccountHistory.date))
        .all()
    )
    if data:
        return {d[0]: float(d[1]) for d in data}

    # Fallback to transaction sums when no history exists
    tx_data = (
        db.session.query(func.date(Transaction.date), func.sum(Transaction.amount))
        .filter(Transaction.user_id == user_id)
        .filter(Transaction.date >= start_date, Transaction.date <= end_date)
        .group_by(func.date(Transaction.date))
        .all()
    )

    running = 0.0
    lookup = {d[0]: float(d[1]) for d in tx_data}
    out = {}
    for i in range((end_date - start_date).days + 1):
        day = start_date + timedelta(days=i)
        running += lookup.get(day, 0.0)
        out[day] = running
    return out
