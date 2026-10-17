# app/routes/recurring.py
import types
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.config import logger
from app.extensions import db
from app.models import Transaction
from app.services.recurring_bridge import RecurringBridge

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


def _error_response(exc):
    """JSON error for a ``RecurringError`` using its own HTTP status."""
    return jsonify({"status": "error", "code": exc.code, "message": str(exc)}), exc.status


def _source_transaction_fields(owner_id, account_id, tx_id):
    """Return ``(description, canonical_delta)`` from an owner-scoped transaction or raise."""
    from app.services import recurring_repository as repo
    from app.services.transaction_semantics import normalize_amount

    tx = Transaction.query.filter_by(transaction_id=tx_id, account_id=account_id).first()
    if tx is None or (tx.user_id and tx.user_id != owner_id):
        raise repo.StreamNotFound("Transaction not found for this account")
    result = normalize_amount(provider=getattr(tx.provider, "value", tx.provider), raw_amount=tx.amount)
    if result.delta is None:
        raise repo.ValidationFailed("Transaction amount direction is unknown; enter the amount manually")
    name = tx.merchant_name if tx.merchant_name not in (None, "", "Unknown") else tx.description
    return name or "Recurring payment", result.delta


@recurring.route("/accounts/<account_id>/recurringTx", methods=["PUT"])
def update_recurring_tx(account_id):
    """Create or update a user-defined recurring plan (legacy shape, backed by recurring streams).

    ``amount`` is the signed cash amount (negative = money out). With ``tx_id`` the description and
    amount come from that owner-scoped transaction; otherwise ``description`` and ``amount`` are
    required. ``user_id`` in the payload is ignored: the owner is configured server-side.
    """
    from app.services import recurring_repository as repo

    try:
        owner_id = repo.trusted_owner_id()
        repo.owned_account(owner_id, account_id)
        data = request.get_json(silent=True) or {}
        tx_id = data.get("tx_id")
        if tx_id:
            description, amount = _source_transaction_fields(owner_id, account_id, tx_id)
        else:
            description = (data.get("description") or "").strip()
            if not description or data.get("amount") is None:
                raise repo.ValidationFailed("description and amount are required without tx_id")
            amount = data.get("amount")
        frequency = data.get("frequency", "monthly")
        next_due = data.get("next_due_date")
        anchor = repo.parse_date(next_due, "next_due_date") if next_due else date.today() + timedelta(days=30)
        notes = data.get("notes", "")

        existing = repo.find_by_name_and_amount(owner_id, account_id, description, amount)
        if len(existing) > 1:
            raise repo.AmbiguousMatch("Several recurring plans match; update one by id")
        if existing:
            repo.update_stream(
                owner_id,
                existing[0].id,
                cadence=frequency,
                notes=notes,
                anchor_date=anchor,
                status="confirmed",
            )
        else:
            repo.create_manual(
                owner_id,
                account_id=account_id,
                display_name=description,
                amount_cash_delta=amount,
                amount_mode=data.get("amount_mode", "fixed"),
                cadence=frequency,
                anchor_date=anchor,
                notes=notes,
            )
        return jsonify({"status": "success", "message": "Recurring transaction saved."}), 200
    except repo.RecurringError as exc:
        return _error_response(exc)
    except Exception as e:
        db.session.rollback()
        logger.error("Error saving recurring transaction: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------
# DELETE /accounts/<account_id>/recurringTx
# Remove a recurring transaction rule
# --------------------------------------


@recurring.route("/accounts/<account_id>/recurringTx", methods=["DELETE"])
def delete_recurring_tx(account_id):
    """End a recurring plan matched by description and amount (legacy shape).

    Several matches return 409: the caller must use the ID-based endpoint instead of guessing.
    """
    from app.services import recurring_repository as repo

    try:
        owner_id = repo.trusted_owner_id()
        data = request.get_json(silent=True) or {}
        description = data.get("description")
        amount = data.get("amount")
        if not description or amount is None:
            return jsonify({"status": "error", "message": "Missing required fields."}), 400

        matches = repo.find_by_name_and_amount(owner_id, account_id, description, amount)
        if not matches:
            return jsonify({"status": "error", "message": "No matching recurring rule found."}), 404
        if len(matches) > 1:
            raise repo.AmbiguousMatch(
                "Multiple recurring rules match this description and amount; delete by stream id instead."
            )
        repo.delete_or_end_stream(owner_id, matches[0].id)
        return jsonify({"status": "success", "message": "Recurring rule deleted."}), 200
    except repo.RecurringError as exc:
        return _error_response(exc)
    except Exception as e:
        db.session.rollback()
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
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=90)
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

        # User-defined reminders come from confirmed recurring streams. Without a configured
        # owner no stream is read (fail closed); auto-detected reminders above are unaffected.
        streams_available = True
        try:
            from app.services import recurring_repository as repo

            owner_id = repo.trusted_owner_id()
            streams = repo.list_streams(owner_id, account_id=account_id, statuses=["confirmed"])
        except repo.RecurringError:
            streams, streams_available = [], False
        for stream in streams:
            next_due = repo.next_due_date(stream, today)
            if next_due is None or not 0 <= (next_due - today).days <= 7:
                continue
            reminders.append(
                {
                    "source": "user",
                    "account_id": account_id,
                    "stream_id": stream.id,
                    "description": stream.display_name,
                    "amount": float(stream.amount_cash_delta),
                    "next_due_date": next_due.strftime("%Y-%m-%d"),
                    "days_until_due": (next_due - today).days,
                    "notes": stream.notes,
                    "frequency": stream.cadence,
                    "auto_detection": {
                        "occurrences": 1,
                        "latest_transaction_date": next_due.strftime("%Y-%m-%d"),
                        "confidence_score": 35,
                    },
                }
            )

        return jsonify({"status": "success", "reminders": reminders, "streams_available": streams_available}), 200

    except Exception as e:
        logger.error(
            "Error fetching structured recurring transactions: %s",
            e,
            exc_info=True,
        )
        return jsonify({"status": "error", "message": str(e)}), 500
