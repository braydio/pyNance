"""HTTP routes for transaction management.

This blueprint exposes endpoints for updating and retrieving transaction
records across all linked accounts.
"""

import json
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from app.config import logger
from app.extensions import db
from app.models import Account, Transaction
from app.sql import account_logic
from flask import Blueprint, jsonify, request
from sqlalchemy import func

transactions = Blueprint("transactions", __name__)

UTC = timezone.utc
TWOPLACES = Decimal("0.01")
AMOUNT_EPSILON = TWOPLACES


def _parse_iso_datetime(value: str) -> datetime:
    """Return a timezone-aware ``datetime`` parsed from ``value``."""

    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Attach UTC timezone information to naive datetimes."""

    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@transactions.route("/update", methods=["PUT"])
def update_transaction():
    """Update a transaction's editable details.

    Allowed fields: ``amount``, ``date``, ``description``, ``category``,
    ``merchant_name``, ``merchant_type`` and ``is_internal``. Account and
    provider identifiers remain immutable.
    """
    try:
        data = request.json
        transaction_id = data.get("transaction_id")
        if not transaction_id:
            return (
                jsonify({"status": "error", "message": "Missing transaction_id"}),
                400,
            )

        txn = Transaction.query.filter_by(transaction_id=transaction_id).first()
        if not txn:
            return jsonify({"status": "error", "message": "Transaction not found"}), 404

        changed_fields = {}
        if "amount" in data:
            try:
                txn.amount = Decimal(str(data["amount"])).quantize(TWOPLACES)
            except (InvalidOperation, TypeError, ValueError):
                return jsonify({"status": "error", "message": "Invalid amount"}), 400
            changed_fields["amount"] = True
        if "date" in data:
            try:
                txn.date = _parse_iso_datetime(data["date"])
            except (TypeError, ValueError):
                return (
                    jsonify({"status": "error", "message": "Invalid date format"}),
                    400,
                )
            changed_fields["date"] = True
        if "description" in data:
            txn.description = data["description"]
            changed_fields["description"] = True
        if "category" in data:
            txn.category = data["category"]
            changed_fields["category"] = True
        if "merchant_name" in data:
            txn.merchant_name = data["merchant_name"]
            changed_fields["merchant_name"] = True
        if "merchant_type" in data:
            txn.merchant_type = data["merchant_type"]
            changed_fields["merchant_type"] = True
        counterpart_id = data.get("counterpart_transaction_id")
        flag_counterpart = data.get("flag_counterpart", False)
        if "is_internal" in data:
            is_internal = bool(data["is_internal"])
            txn.is_internal = is_internal
            txn.internal_match_id = (
                counterpart_id if is_internal and counterpart_id else None
            )
            changed_fields["is_internal"] = True
            if counterpart_id:
                other = Transaction.query.filter_by(
                    transaction_id=counterpart_id
                ).first()
                if other and flag_counterpart:
                    other.is_internal = is_internal
                    other.internal_match_id = (
                        txn.transaction_id if is_internal else None
                    )

        txn.user_modified = True
        existing_fields = {}
        if txn.user_modified_fields:
            existing_fields = json.loads(txn.user_modified_fields)
        for field in changed_fields:
            existing_fields[field] = True
        txn.user_modified_fields = json.dumps(existing_fields)

        db.session.commit()

        # Optional: save as a reusable rule with richer scoping
        if data.get("save_as_rule"):
            from app.sql import transaction_rules_logic

            field = data.get("rule_field")  # e.g., "category" or "merchant_name"
            value = data.get("rule_value")  # desired value to set
            description = data.get("rule_description") or txn.description
            account_scope = data.get("rule_account_id") or txn.account_id

            match_criteria = {"account_id": account_scope}
            if description:
                # Exact-match description pattern
                import re

                escaped = re.escape(description)
                match_criteria["description_pattern"] = f"^{escaped}$"

            action = {}
            if field == "category":
                # Try to set both category and category_id coherently
                action["category"] = value or txn.category
                if txn.category_id:
                    action["category_id"] = txn.category_id
            elif field in ("merchant_name", "merchant_type"):
                action[field] = value or getattr(txn, field)

            transaction_rules_logic.create_rule(txn.user_id, match_criteria, action)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error updating transaction: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@transactions.route("/scan-internal", methods=["POST"])
def scan_internal_transfers():
    """Detect potential internal transfer pairs without mutating records."""
    try:
        txns = Transaction.query.filter(
            (Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None))
        ).all()
        pairs = []
        seen = set()
        for txn in txns:
            if txn.transaction_id in seen:
                continue
            account = Account.query.filter_by(account_id=txn.account_id).first()
            if not account:
                continue
            start = txn.date - timedelta(days=1)
            end = txn.date + timedelta(days=1)
            counterpart = (
                db.session.query(Transaction)
                .join(Account, Transaction.account_id == Account.account_id)
                .filter(Account.user_id == account.user_id)
                .filter(Transaction.account_id != txn.account_id)
                .filter(Transaction.date >= start)
                .filter(Transaction.date <= end)
                .filter(func.abs(Transaction.amount + txn.amount) <= AMOUNT_EPSILON)
                .filter(Transaction.is_internal.is_(False))
                .first()
            )
            if counterpart and counterpart.transaction_id not in seen:
                pairs.append(
                    {
                        "transaction_id": txn.transaction_id,
                        "counterpart_id": counterpart.transaction_id,
                        "amount": float(txn.amount),
                        "date": txn.date.isoformat(),
                        "description": txn.description,
                        "counterpart": {
                            "transaction_id": counterpart.transaction_id,
                            "amount": float(counterpart.amount),
                            "date": counterpart.date.isoformat(),
                            "description": counterpart.description,
                        },
                    }
                )
                seen.add(txn.transaction_id)
                seen.add(counterpart.transaction_id)

        return jsonify({"status": "success", "pairs": pairs}), 200
    except Exception as e:
        logger.error(f"Error scanning internal transfers: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@transactions.route("/user_modify/update")
def user_modified_update_transaction():
    """
    Update a transaction's editable details.
    """
    try:
        data = request.json
        transaction_id = data.get("transaction_id")
        if not transaction_id:
            return (
                jsonify({"status": "error", "message": "Missing transaction_id"}),
                400,
            )

        txn = Transaction.query.filter_by(transaction_id=transaction_id).first()
        if not txn:
            return jsonify({"status": "error", "message": "Transaction not found"}), 404

        changed_fields = {}
        if "amount" in data:
            try:
                txn.amount = Decimal(str(data["amount"])).quantize(TWOPLACES)
            except (InvalidOperation, TypeError, ValueError):
                return jsonify({"status": "error", "message": "Invalid amount"}), 400
            changed_fields["amount"] = True
        if "date" in data:
            try:
                txn.date = _parse_iso_datetime(data["date"])
            except (TypeError, ValueError):
                return (
                    jsonify({"status": "error", "message": "Invalid date format"}),
                    400,
                )
            changed_fields["date"] = True
        if "description" in data:
            txn.description = data["description"]
            changed_fields["description"] = True
        if "category" in data:
            txn.category = data["category"]
            changed_fields["category"] = True
        if "merchant_name" in data:
            txn.merchant_name = data["merchant_name"]
            changed_fields["merchant_name"] = True
        if "merchant_type" in data:
            txn.merchant_type = data["merchant_type"]
            changed_fields["merchant_type"] = True

        txn.user_modified = True
        existing_fields = {}
        if txn.user_modified_fields:
            existing_fields = json.loads(txn.user_modified_fields)
        for field in changed_fields:
            existing_fields[field] = True
        txn.user_modified_fields = json.dumps(existing_fields)

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error updating transaction: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@transactions.route("/get_transactions", methods=["GET"])
def get_transactions_paginated():
    """Return paginated transactions with optional filters.

    Accepted query parameters include:
    ``start_date`` and ``end_date`` (YYYY-MM-DD), ``account_ids`` as a
    comma-separated string, and ``tx_type`` (``credit`` or ``debit``).
    Unknown or empty parameters are ignored.
    """
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        category = request.args.get("category")
        account_ids_str = request.args.get("account_ids")
        tx_type = request.args.get("tx_type") or request.args.get("type")

        start_date = _ensure_utc(
            datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        )
        end_date = _ensure_utc(
            (
                datetime.strptime(end_date_str, "%Y-%m-%d")
                + timedelta(days=1)
                - timedelta(microseconds=1)
            )
            if end_date_str
            else None
        )

        transactions, total = account_logic.get_paginated_transactions(
            page,
            page_size,
            start_date=start_date,
            end_date=end_date,
            category=category,
            account_ids=account_ids_str.split(",") if account_ids_str else None,
            tx_type=tx_type,
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"transactions": transactions, "total": total},
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error in get_transactions_paginated: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@transactions.route("/<account_id>/transactions", methods=["GET"])
def get_account_transactions(account_id):
    """Return transactions for a specific account."""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        category = request.args.get("category")
        recent = request.args.get("recent") == "true"
        limit = int(request.args.get("limit", 10))

        start_date = _ensure_utc(
            datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        )
        logger.debug(
            f"Changed date string {start_date_str} to datetime object: {start_date}"
        )

        end_date = _ensure_utc(
            (
                datetime.strptime(end_date_str, "%Y-%m-%d")
                + timedelta(days=1)
                - timedelta(microseconds=1)
            )
            if end_date_str
            else None
        )
        logger.debug(
            f"Changed date string {end_date_str} to datetime object: {end_date}"
        )
        # Ignore date filters when fetching recent transactions
        if recent:
            start_date = None
            end_date = None

        transactions, total = account_logic.get_paginated_transactions(
            page,
            page_size,
            start_date=start_date,
            end_date=end_date,
            category=category,
            account_id=account_id,
            recent=recent,
            limit=limit,
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"transactions": transactions, "total": total},
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error in get_account_transactions: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@transactions.route("/merchants", methods=["GET"])
def merchant_suggestions():
    """Return a list of merchant name suggestions.

    Query params:
    - q: optional substring filter (case-insensitive)
    - limit: max number of results (default 50)
    """
    try:
        q = (request.args.get("q") or "").strip()
        limit = min(int(request.args.get("limit", 50)), 200)

        query = db.session.query(
            Transaction.merchant_name, func.count(Transaction.id).label("cnt")
        ).group_by(Transaction.merchant_name)

        if q:
            query = query.filter(Transaction.merchant_name.ilike(f"%{q}%"))

        rows = (
            query.order_by(func.count(Transaction.id).desc(), Transaction.merchant_name.asc())
            .limit(limit)
            .all()
        )
        names = [name for name, _ in rows if name]
        return jsonify({"status": "success", "data": names}), 200
    except Exception as e:
        logger.error(f"Error fetching merchant suggestions: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@transactions.route("/rules", methods=["POST"])
def create_rule():
    """Create a transaction rule from user edits.

    Body: {
      user_id, field, value, description, account_id
    }
    """
    try:
        payload = request.get_json() or {}
        user_id = payload.get("user_id")
        field = payload.get("field")
        value = payload.get("value")
        description = payload.get("description")
        account_id = payload.get("account_id")
        if not user_id or not field or (not value and value != ""):
            return (
                jsonify({"status": "error", "message": "Missing required fields"}),
                400,
            )

        from app.sql import transaction_rules_logic

        match = {}
        if account_id:
            match["account_id"] = account_id
        if description:
            import re

            match["description_pattern"] = f"^{re.escape(description)}$"

        action = {field: value}
        rule = transaction_rules_logic.create_rule(user_id, match, action)
        return jsonify({"status": "success", "rule_id": rule.id}), 201
    except Exception as e:
        logger.error(f"Error creating rule: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@transactions.route("/manual", methods=["GET"])
def get_manual_transactions():
    """Return all transactions from manually managed accounts."""
    try:
        from app.utils.finance_utils import display_transaction_amount

        manual_txns = (
            db.session.query(Transaction)
            .join(Account, Transaction.account_id == Account.account_id)
            .filter(Account.link_type.in_(["manual", "pdf_import"]))
            .filter(Account.is_hidden.is_(False))
            .order_by(Transaction.date.desc())
            .all()
        )

        results = [
            {
                "transaction_id": t.transaction_id,
                "date": t.date.isoformat(),
                "name": t.description,
                "amount": display_transaction_amount(t),
                "type": t.merchant_type,
                "provider": t.account.link_type if t.account else None,
                "account_id": t.account_id,
                "account_name": getattr(t.account, "name", None),
            }
            for t in manual_txns
        ]

        return jsonify(results)
    except Exception as e:
        logger.error("Error fetching manual transactions:\n%s", traceback.format_exc())
        return jsonify({"error": str(e)}), 500
