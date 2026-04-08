# app/routes/recurring.py
import types
from datetime import date, datetime, timedelta, timezone

from app.config import logger
from app.extensions import db
from app.models import RecurringTransaction, Transaction
from app.services.recurring_bridge import RecurringBridge
from flask import Blueprint, jsonify, request
from sqlalchemy import func

recurring = Blueprint("recurring", __name__)

# --------------------------------------
# Utility
# --------------------------------------


def add_months(original_date, months=1):
    new_month = original_date.month + months
    new_year = original_date.year
    while new_month > 12:
        new_month -= 12
        new_year += 1
    try:
        return original_date.replace(year=new_year, month=new_month)
    except ValueError:
        return original_date.replace(year=new_year, month=new_month, day=28)


def _build_auto_confidence_score(occurrences, latest_date, recent_cutoff, today):
    """Score auto-detected recurring confidence from history depth and recency.

    Args:
        occurrences (int): Number of matching transactions in the recent window.
        latest_date (date): Most recent observed transaction date for the pattern.
        recent_cutoff (date): Inclusive lower bound used for detection.
        today (date): Current day.

    Returns:
        int: Confidence score on a 0-100 scale.
    """
    occurrence_score = min(max(occurrences - 1, 0) * 15, 60)
    lookback_days = max((today - recent_cutoff).days, 1)
    recency_days = max((today - latest_date).days, 0)
    recency_ratio = max(0.0, 1 - (recency_days / lookback_days))
    recency_score = round(recency_ratio * 40)
    return max(0, min(100, occurrence_score + recency_score))


# --------------------------------------
# PUT /accounts/<account_id>/recurringTx
# Save or update a recurring transaction
# --------------------------------------


@recurring.route("/accounts/<account_id>/recurringTx", methods=["PUT"])
def update_recurring_tx(account_id):
    """Create or update a user-defined recurring transaction."""
    try:
        data = request.json or {}
        tx_id = data.get("tx_id")
        amount = data.get("amount", 0.0)
        description = data.get("description", "Untitled Recurring")
        frequency = data.get("frequency", "monthly")
        notes = data.get("notes", "")
        next_due_str = data.get("next_due_date")

        # Resolve account ID from tx_id if available
        if tx_id:
            tx = Transaction.query.filter_by(transaction_id=tx_id).first()
            account_id = tx.account_id if tx else account_id

        try:
            next_due_date = (
                datetime.strptime(next_due_str, "%Y-%m-%d").date()
                if next_due_str
                else date.today() + timedelta(days=30)
            )
        except Exception as e:
            logger.warning("Invalid date format for 'next_due_date': %s", e)
            next_due_date = date.today() + timedelta(days=30)

        existing = RecurringTransaction.query.filter_by(
            account_id=account_id, description=description, amount=amount
        ).first()

        if existing:
            existing.frequency = frequency
            existing.notes = notes
            existing.next_due_date = next_due_date
        else:
            db.session.add(
                RecurringTransaction(
                    account_id=account_id,
                    description=description,
                    amount=amount,
                    frequency=frequency,
                    next_due_date=next_due_date,
                    notes=notes,
                )
            )

        db.session.commit()
        return (
            jsonify({"status": "success", "message": "Recurring transaction saved."}),
            200,
        )

    except Exception as e:
        logger.error("Error saving recurring transaction: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------
# DELETE /accounts/<account_id>/recurringTx
# Remove a recurring transaction rule
# --------------------------------------


@recurring.route("/accounts/<account_id>/recurringTx", methods=["DELETE"])
def delete_recurring_tx(account_id):
    """Delete a user-defined recurring transaction."""
    try:
        data = request.get_json() or {}
        description = data.get("description")
        amount = data.get("amount")

        if not description or amount is None:
            return (
                jsonify({"status": "error", "message": "Missing required fields."}),
                400,
            )

        match = RecurringTransaction.query.filter_by(
            account_id=account_id, description=description, amount=amount
        ).first()

        if not match:
            return (
                jsonify({"status": "error", "message": "No matching recurring rule found."}),
                404,
            )

        db.session.delete(match)
        db.session.commit()
        return jsonify({"status": "success", "message": "Recurring rule deleted."}), 200

    except Exception as e:
        logger.error("Failed to delete recurring transaction: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------
# POST /scan/<account_id>
# Auto-detect recurring transactions
# --------------------------------------


@recurring.route("/scan/<account_id>", methods=["POST"])
def scan_account_for_recurring(account_id):
    """Detect recurring transactions for an account and persist them."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        rows = (
            Transaction.query.filter_by(account_id=account_id)
            .filter(Transaction.date >= cutoff)
            .order_by(Transaction.date.desc())
            .all()
        )
        from app.utils.finance_utils import display_transaction_amount

        txs = [
            {
                "amount": display_transaction_amount(tx),
                "description": tx.description or tx.merchant_name or "",
                "date": tx.date.strftime("%Y-%m-%d"),
            }
            for tx in rows
        ]

        rb = RecurringBridge(txs)
        rb.sync_to_db()
        return get_structured_recurring(account_id)
    except Exception as e:
        logger.error(
            "Error scanning account %s for recurring: %s",
            account_id,
            e,
            exc_info=True,
        )
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------
# GET /<account_id>/recurring
# Fetch all (user + auto) upcoming reminders
# --------------------------------------


@recurring.route("/<account_id>/recurring", methods=["GET"])
def get_structured_recurring(account_id):
    """Return a list of upcoming recurring payment reminders (user-defined + auto-detected)."""
    try:
        from app.utils.finance_utils import display_transaction_amount

        today = date.today()
        recent_cutoff = today - timedelta(days=90)
        reminders = []

        # Auto-detected reminders
        auto_rows = (
            db.session.query(
                Transaction.description,
                Transaction.amount,
                func.count(Transaction.id).label("occurrences"),
                func.max(Transaction.date).label("latest_date"),
            )
            .filter(Transaction.account_id == account_id)
            .filter(Transaction.date >= recent_cutoff)
            .group_by(Transaction.description, Transaction.amount)
            .having(func.count(Transaction.id) >= 2)
            .all()
        )

        for row in auto_rows:
            latest_date = (
                row.latest_date
                if isinstance(row.latest_date, date)
                else datetime.strptime(row.latest_date, "%Y-%m-%d").date()
            )
            next_due = add_months(latest_date, 1)
            if isinstance(next_due, datetime):
                next_due = next_due.date()
            if 0 <= (next_due - today).days <= 7:
                confidence_score = _build_auto_confidence_score(
                    occurrences=row.occurrences,
                    latest_date=latest_date,
                    recent_cutoff=recent_cutoff,
                    today=today,
                )
                dummy_tx = types.SimpleNamespace(amount=row.amount)
                reminders.append(
                    {
                        "source": "auto",
                        "account_id": account_id,
                        "description": row.description,
                        "amount": display_transaction_amount(dummy_tx),
                        "next_due_date": next_due.strftime("%Y-%m-%d"),
                        "days_until_due": (next_due - today).days,
                        "auto_detection": {
                            "occurrences": row.occurrences,
                            "latest_transaction_date": latest_date.strftime("%Y-%m-%d"),
                            "confidence_score": confidence_score,
                        },
                    }
                )

        # User-defined reminders
        user_rows = RecurringTransaction.query.filter_by(account_id=account_id).all()
        for row in user_rows:
            if not row.next_due_date:
                continue
            next_due = row.next_due_date
            if 0 <= (next_due - today).days <= 7:
                getattr(row, "transaction", row)
                reminders.append(
                    {
                        "source": "user",
                        "account_id": account_id,
                        "description": row.description,
                        "amount": display_transaction_amount(row),
                        "next_due_date": next_due.strftime("%Y-%m-%d"),
                        "days_until_due": (next_due - today).days,
                        "notes": row.notes,
                        "frequency": row.frequency,
                        "auto_detection": {
                            "occurrences": 1,
                            "latest_transaction_date": next_due.strftime("%Y-%m-%d"),
                            "confidence_score": 35,
                        },
                    }
                )

        return jsonify({"status": "success", "reminders": reminders}), 200

    except Exception as e:
        logger.error(
            "Error fetching structured recurring transactions: %s",
            e,
            exc_info=True,
        )
        return jsonify({"status": "error", "message": str(e)}), 500
