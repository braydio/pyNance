"""HTTP routes for transaction management.

This blueprint exposes endpoints for updating and retrieving transaction
records across all linked accounts.
"""

import json
import traceback
from datetime import datetime

from app.config import logger
from app.extensions import db
from app.models import Account, Transaction
from app.sql import account_logic
from flask import Blueprint, jsonify, request

transactions = Blueprint("transactions", __name__)


@transactions.route("/update", methods=["PUT"])
def update_transaction():
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
            txn.amount = float(data["amount"])
            changed_fields["amount"] = True
        if "date" in data:
            txn.date = data["date"]
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
            txn.amount = float(data["amount"])
            changed_fields["amount"] = True
        if "date" in data:
            txn.date = data["date"]
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
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        category = request.args.get("category")

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else None
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        )

        transactions, total = account_logic.get_paginated_transactions(
            page,
            page_size,
            start_date=start_date,
            end_date=end_date,
            category=category,
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
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else None
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        )

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
    try:
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
                "amount": t.amount,
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
