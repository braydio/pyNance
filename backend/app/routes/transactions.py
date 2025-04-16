# File: app/routes/transactions.py

import json
from datetime import datetime

import requests
from app.config import FILES, logger
from app.extensions import db
from app.helpers.teller_helpers import load_tokens  # Use the shared helper
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
    """
    Return paginated transactions.
    """
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))
        transactions_list, total = account_logic.get_paginated_transactions(
            page, page_size
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"transactions": transactions_list, "total": total},
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


