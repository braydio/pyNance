from datetime import date, datetime, timedelta

from app.config import logger
from app.extensions import db
from app.models import RecurringTransaction, Transaction
from flask import Blueprint, jsonify, request
from sqlalchemy import func

recurring = Blueprint("recurring", __name__)


# -------------------------------------------------------------------
# 1) Save or update a user-defined recurring transaction
# -------------------------------------------------------------------
@recurring.route("/<account_id>/recurringTx", methods=["PUT"])
def update_recurring_tx(account_id):
    """
    Create or update a RecurringTransaction row.
    The body can include: { amount, description, frequency, notes, next_due_date }
    """
    try:
        data = request.json or {}
        logger.debug(
            f"Received user-defined recurring transaction for account {account_id}, data={data}"
        )

        amount = data.get("amount", 0.0)
        description = data.get("description", "Untitled Recurring")
        frequency = data.get("frequency", "monthly")
        notes = data.get("notes", "")

        next_due_str = data.get("next_due_date")
        if next_due_str:
            try:
                next_due_date = datetime.strptime(next_due_str, "%Y-%m-%d").date()
            except Exception as e:
                logger.warning(f"Invalid 'next_due_date' format, ignoring: {e}")
                next_due_date = date.today() + timedelta(days=30)
        else:
            next_due_date = date.today() + timedelta(days=30)

        existing = RecurringTransaction.query.filter_by(
            account_id=account_id, description=description, amount=amount
        ).first()
        if existing:
            logger.debug(
                f"Updating existing RecurringTransaction for account {account_id}"
            )
            existing.frequency = frequency
            existing.notes = notes
            existing.next_due_date = next_due_date
            db.session.commit()
        else:
            logger.debug(f"Inserting new RecurringTransaction for account {account_id}")
            new_rec = RecurringTransaction(
                account_id=account_id,
                description=description,
                amount=amount,
                frequency=frequency,
                next_due_date=next_due_date,
                notes=notes,
            )
            db.session.add(new_rec)
            db.session.commit()

        return (
            jsonify({"status": "success", "message": "Recurring transaction saved."}),
            200,
        )

    except Exception as e:
        logger.error(
            f"Error saving user-defined recurring transaction: {e}", exc_info=True
        )
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------------
# 2) Fetch merged recurring transactions (user + auto-detected), return reminders
# -------------------------------------------------------------------


@recurring.route("/<account_id>/recurring", methods=["GET"])
def get_structured_recurring(account_id):
    """
    Return a list of structured reminders for:
      A) Auto-detected recurring transactions from recent history
      B) User-defined recurring transactions
    Each entry includes: source, description, amount, next_due_date
    """
    try:
        today = date.today()
        three_months_ago = today - timedelta(days=90)
        reminders = []

        # AUTO-DETECTED
        auto_rows = (
            db.session.query(
                Transaction.description,
                Transaction.amount,
                func.count(Transaction.id).label("occurrences"),
                func.max(Transaction.date).label("latest_date"),
            )
            .filter(Transaction.account_id == account_id)
            .filter(Transaction.date >= three_months_ago)
            .group_by(Transaction.description, Transaction.amount)
            .having(func.count(Transaction.id) >= 2)
            .all()
        )

        for row in auto_rows:
            if not isinstance(row.latest_date, date):
                latest_date = datetime.strptime(row.latest_date, "%Y-%m-%d").date()
            else:
                latest_date = row.latest_date
            next_due = add_months(latest_date, 1)
            if 0 <= (next_due - today).days <= 7:
                reminders.append(
                    {
                        "source": "auto",
                        "description": row.description,
                        "amount": float(row.amount),
                        "next_due_date": next_due.strftime("%Y-%m-%d"),
                    }
                )

        # USER-DEFINED
        user_rows = RecurringTransaction.query.filter_by(account_id=account_id).all()
        for row in user_rows:
            if not row.next_due_date:
                continue
            next_due = row.next_due_date
            if 0 <= (next_due - today).days <= 7:
                reminders.append(
                    {
                        "source": "user",
                        "description": row.description,
                        "amount": float(row.amount),
                        "next_due_date": next_due.strftime("%Y-%m-%d"),
                        "notes": row.notes,
                        "frequency": row.frequency,
                    }
                )

        return jsonify({"status": "success", "reminders": reminders}), 200

    except Exception as e:
        logger.error(
            f"Error fetching structured recurring transactions: {e}", exc_info=True
        )
        return jsonify({"status": "error", "message": str(e)}), 500


def add_months(original_date, months=1):
    new_month = original_date.month + months
    new_year = original_date.year
    while new_month > 12:
        new_month -= 12
        new_year += 1
    try:
        return original_date.replace(year=new_year, month=new_month)
    except ValueError:
        day = min(original_date.day, 28)
        return original_date.replace(year=new_year, month=new_month, day=day)
