# File: app/routes/transactions.py
from flask import Blueprint, jsonify, request
from datetime import datetime
import json
import traceback
from app.config import FILES, logger
from app.models import Account, Transaction
from app.sql import account_logic
from app.extensions import db

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
            return jsonify(
                {"status": "error", "message": "Missing transaction_id"}
            ), 400

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
            return jsonify(
                {"status": "error", "message": "Missing transaction_id"}
            ), 400

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
    """Return paginated transactions."""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))

        if page < 1 or page_size < 1:
            raise ValueError("Page and page_size must be positive integers")

        transactions_list, total = account_logic.get_paginated_transactions(
            page, page_size
        )

        return jsonify(
            {
                "status": "success",
                "data": {"transactions": transactions_list, "total": total},
            },
            200,
        )

    except ValueError as ve:
        logger.warning(f"Invalid pagination input: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400

    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@transactions.route("/manual", methods=["GET"])
def get_manual_transactions():
    try:
        manual_txns = (
            db.session.query(Transaction)
            .join(Account, Transaction.account_id == Account.account_id)
            .filter(Account.link_type.in_(["manual", "pdf_import"]))
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
