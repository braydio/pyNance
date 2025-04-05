# File: app/routes/transactions.py

import json
from datetime import datetime

import requests
from app.config import FILES, TELLER_API_BASE_URL, logger
from app.extensions import db
from app.helpers.teller_helpers import load_tokens  # Use the shared helper
from app.models import Account, Transaction
from app.sql import account_logic
from flask import Blueprint, jsonify, request

transactions = Blueprint("transactions", __name__)

@transactions.route("/get_transactions", methods=["GET"])
def get_transactions():
    """
    Return paginated transactions.
    """
    try:
        # safely get query params with defaults
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))

        # get your data from whatever your logic layer is
        transactions_list, total = account_logic.get_paginated_transactions(page, page_size)

        return jsonify({
            "status": "success",
            "data": {
                "transactions": transactions_list,
                "total": total
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
