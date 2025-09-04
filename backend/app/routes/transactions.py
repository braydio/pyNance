"""HTTP routes for transaction management.

This blueprint exposes endpoints for updating and retrieving transaction
records across all linked accounts.
"""

import json
import traceback
from datetime import datetime, timedelta

from app.config import logger
from app.extensions import db
from app.models import Account, Transaction
from app.sql import account_logic
from flask import Blueprint, jsonify, request
from sqlalchemy import func

transactions = Blueprint("transactions", __name__)


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
                txn.amount = float(data["amount"])
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Invalid amount"}), 400
            changed_fields["amount"] = True
        if "date" in data:
            try:
                txn.date = datetime.fromisoformat(data["date"])
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

        if data.get("save_as_rule"):
            from app.sql import transaction_rules_logic

            criteria = {"merchant_name": txn.merchant_name}
            action = {"category": txn.category, "category_id": txn.category_id}
            transaction_rules_logic.create_rule(txn.user_id, criteria, action)
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
                .filter(func.abs(Transaction.amount + txn.amount) <= 0.01)
                .filter(Transaction.is_internal.is_(False))
                .first()
            )
            if counterpart and counterpart.transaction_id not in seen:
                pairs.append(
                    {
                        "transaction_id": txn.transaction_id,
                        "counterpart_id": counterpart.transaction_id,
                        "amount": txn.amount,
                        "date": txn.date.isoformat(),
                        "description": txn.description,
                        "counterpart": {
                            "transaction_id": counterpart.transaction_id,
                            "amount": counterpart.amount,
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
                txn.amount = float(data["amount"])
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Invalid amount"}), 400
            changed_fields["amount"] = True
        if "date" in data:
            try:
                txn.date = datetime.fromisoformat(data["date"])
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
    """Return paginated transactions with optional filters."""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        category = request.args.get("category")
        account_ids_str = request.args.get("account_ids")
        tx_type = request.args.get("tx_type")

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d")
            + timedelta(days=1)
            - timedelta(microseconds=1)
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

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        )
        logger.debug(
            f"Changed date string {start_date_str} to datetime object: {start_date}"
        )

        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d")
            + timedelta(days=1)
            - timedelta(microseconds=1)
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
