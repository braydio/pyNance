"""
recurring.py

Provides routes to handle both:
(1) User-defined recurring transactions (stored in RecurringTransaction table)
(2) Auto-detected recurring transactions (pattern-based from main Transaction table)
Then merges both for a single reminders list.
"""

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
@recurring.route("<account_id>/recurringTx", methods=["PUT"])
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

        # Minimal required fields
        amount = data.get("amount", 0.0)
        description = data.get("description", "Untitled Recurring")
        frequency = data.get("frequency", "monthly")
        notes = data.get("notes", "")

        # If next_due_date not provided, default to ~30 days from now
        next_due_str = data.get("next_due_date")
        if next_due_str:
            try:
                next_due_date = datetime.strptime(next_due_str, "%Y-%m-%d").date()
            except Exception as e:
                logger.warning(f"Invalid 'next_due_date' format, ignoring: {e}")
                next_due_date = date.today() + timedelta(days=30)
        else:
            next_due_date = date.today() + timedelta(days=30)

        # Try updating an existing recurring transaction with same (account_id, description, amount),
        # otherwise create a new record.
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
def get_merged_recurring(account_id):
    """
    Return a merged list of reminders for:
      A) Auto-detected recurring transactions from main Transaction table
      B) User-defined recurring transactions from RecurringTransaction table
    within the next 7 days
    """
    try:
        today = date.today()
        # ================  AUTO-DETECTED RECURRING  =====================
        three_months_ago = today - timedelta(days=90)

        auto_query = (
            db.session.query(
                Transaction.description,
                Transaction.amount,
                func.count(Transaction.id).label("occurrences"),
                func.max(Transaction.date).label("latest_date"),
            )
            .filter(Transaction.account_id == account_id)
            # If Transaction.date is stored as string, parse carefully or confirm it's a date
            .filter(Transaction.date >= three_months_ago)
            .group_by(Transaction.description, Transaction.amount)
            .having(func.count(Transaction.id) >= 2)
            .all()
        )

        auto_reminders = []
        for row in auto_query:
            latest = row.latest_date
            # If row.latest_date is string, parse it
            if isinstance(latest, str):
                latest = datetime.strptime(latest, "%Y-%m-%d").date()

            next_due_date = add_months(latest, 1)
            days_until_due = (next_due_date - today).days
            if 0 <= days_until_due <= 7:
                auto_reminders.append(
                    f"Reminder (Auto): {row.description} (${row.amount:.2f}) due on {next_due_date.strftime('%b %d')}."
                )

        # ================  USER-DEFINED RECURRING  =====================
        user_rows = RecurringTransaction.query.filter_by(account_id=account_id).all()
        user_reminders = []
        for ur in user_rows:
            # If no next_due_date set, skip
            if not ur.next_due_date:
                continue
            days_until_due = (ur.next_due_date - today).days
            if 0 <= days_until_due <= 7:
                user_reminders.append(
                    f"Reminder (User): {ur.description} (${ur.amount:.2f}) is due on {ur.next_due_date.strftime('%b %d')}."
                )

        # Merge the two sets of reminders
        reminders = auto_reminders + user_reminders

        return jsonify({"status": "success", "reminders": reminders}), 200

    except Exception as e:
        logger.error(
            f"Error fetching merged recurring transactions: {e}", exc_info=True
        )
        return jsonify({"status": "error", "message": str(e)}), 500


# Helper function: add X months (default=1) to a date
def add_months(original_date, months=1):
    """
    Utility: add X months to a given date, carefully handling year rollover.
    """
    new_month = original_date.month + months
    new_year = original_date.year
    while new_month > 12:
        new_month -= 12
        new_year += 1

    try:
        return original_date.replace(year=new_year, month=new_month)
    except ValueError:
        # In case day is out of range for that month, clamp to last day (e.g. 31 -> 30)
        # This is optional logic if you want to handle 31 -> 30 scenarios gracefully
        # Simplify to day=1 or something if you prefer
        day = min(original_date.day, 28)
        return original_date.replace(year=new_year, month=new_month, day=day)
