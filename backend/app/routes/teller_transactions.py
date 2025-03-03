# File: app/routes/teller_transactions.py
import json
from datetime import datetime

import requests
from app.config import FILES, TELLER_API_BASE_URL, logger
from app.extensions import db
from app.models import (  # TellerItem is our new table for Teller-specific data
    Account,
    Transaction,
)
from app.sql import account_logic

from flask import Blueprint, jsonify, request

# Define file paths and API endpoints
TELLER_DOT_KEY = FILES["TELLER_DOT_KEY"]
TELLER_DOT_CERT = FILES["TELLER_DOT_CERT"]
TELLER_TOKENS = FILES["TELLER_TOKENS"]
TELLER_ACCOUNTS = FILES["TELLER_ACCOUNTS"]


def load_tokens():
    try:
        logger.debug(f"Attempting to load tokens from {TELLER_TOKENS}")
        with open(TELLER_TOKENS, "r") as f:
            tokens = json.load(f)
            logger.debug(f"Loaded tokens: {tokens}")
            return tokens
    except FileNotFoundError:
        logger.warning(
            f"Tokens file not found at {TELLER_TOKENS}, returning empty list."
        )
        return []
    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding tokens file at {TELLER_TOKENS}: {e}", exc_info=True
        )
        return []


def save_tokens(tokens):
    try:
        logger.debug(f"Saving tokens to {TELLER_TOKENS}: {tokens}")
        with open(TELLER_TOKENS, "w") as f:
            json.dump(tokens, f, indent=4)
        logger.debug("Tokens saved successfully.")
    except Exception as e:
        logger.error(f"Error saving tokens to {TELLER_TOKENS}: {e}", exc_info=True)


teller_transactions = Blueprint("teller_transactions", __name__)


@teller_transactions.route("/exchange_public_token", methods=["POST"])
def teller_exchange_public_token():
    """
    Exchange a public token for a Teller access token.
    """
    try:
        logger.debug("Exchanging Teller public token for access token.")
        data = request.json
        public_token = data.get("public_token")
        if not public_token:
            logger.error("Missing public token in request.")
            return jsonify({"error": "Missing public token"}), 400

        url = f"{TELLER_API_BASE_URL}/link_tokens/exchange"
        headers = {"Authorization": f"Bearer {FILES['TELLER_DOT_KEY']}"}
        payload = {"public_token": public_token}
        logger.debug(f"Teller exchange payload: {payload}")
        resp = requests.post(url, headers=headers, json=payload)
        logger.debug(f"Teller exchange response: {resp.status_code} - {resp.text}")
        if resp.status_code != 200:
            logger.error(f"Error exchanging public token: {resp.json()}")
            return jsonify({"error": resp.json()}), resp.status_code

        access_token = resp.json().get("access_token")
        user_id = resp.json().get("user", {}).get("id")
        # (For now we store tokens in a JSON file; later you may migrate these to the DB.)
        try:
            with open(FILES["TELLER_TOKENS"], "r") as f:
                tokens = json.load(f)
        except Exception:
            tokens = []
        tokens.append({"user_id": user_id, "access_token": access_token})
        with open(FILES["TELLER_TOKENS"], "w") as f:
            json.dump(tokens, f, indent=4)
        return (
            jsonify(
                {"status": "success", "access_token": access_token, "user_id": user_id}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error in Teller token exchange: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@teller_transactions.route("/refresh_accounts", methods=["POST"])
def teller_refresh_accounts():
    """
    Refresh Teller accounts and transactions.
    For each account in the database, use the Teller token.
    Updated data is stored in the Accounts table.
    """
    try:
        logger.debug("Refreshing Teller accounts from database.")
        accounts = Account.query.all()
        updated_accounts = []
        try:
            with open(FILES["TELLER_TOKENS"], "r") as f:
                tokens = json.load(f)
        except Exception:
            tokens = []
        for account in accounts:
            access_token = None
            for token in tokens:
                if token.get("user_id") == account.user_id:
                    access_token = token.get("access_token")
                    break
            if not access_token:
                logger.warning(f"No access token found for user {account.user_id}")
                continue
            logger.debug(
                f"Refreshing Teller account {account.name} {account.account_id} using token: {access_token}"
            )
            updated = account_logic.refresh_data_for_teller_account(
                account,
                access_token,
                FILES["TELLER_DOT_CERT"],
                FILES["TELLER_DOT_KEY"],
                TELLER_API_BASE_URL,
            )
            if updated:
                updated_accounts.append(account.name)
                # Update the Account record's last_refreshed timestamp
                account.last_refreshed = datetime.utcnow()
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Teller account data refreshed",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing Teller accounts: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@teller_transactions.route("/get_transactions", methods=["GET"])
def teller_get_transactions():
    """
    Return paginated Teller transactions.
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
        logger.error(f"Error fetching Teller transactions: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@teller_transactions.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        logger.debug("Fetching accounts from the database.")
        accounts = account_logic.get_accounts_from_db()  # use our helper
        logger.debug(f"Fetched {len(accounts)} accounts from DB.")
        return jsonify({"status": "success", "data": {"accounts": accounts}}), 200
    except Exception as e:
        logger.error(f"Error fetching accounts from DB: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_transactions.route("/refresh_balances", methods=["POST"])
def refresh_balances():
    """
    For each account in the database, this endpoint calls the Teller API
    to fetch the latest balances (using the -u style authentication) and then
    updates the historical balances (AccountHistory) in the DB.
    """
    try:
        accounts = account_logic.get_accounts_from_db()  # Fetch account details
        updated_accounts = []
        tokens = load_tokens()  # Assumes tokens are stored and retrievable

        for acc in accounts:
            # Find the corresponding Account object
            account = Account.query.filter_by(account_id=acc["account_id"]).first()
            if not account:
                logger.warning(f"Account {acc['account_id']} not found in DB.")
                continue

            # Find the access token for the account's user.
            access_token = None
            for token in tokens:
                if token.get("user_id") == acc["user_id"]:
                    access_token = token.get("access_token")
                    break

            if not access_token:
                logger.warning(f"No access token found for account {acc['account_id']}")
                continue

            # Use our existing refresh logic to fetch balances & update history.
            updated = account_logic.refresh_data_for_teller_account(
                account,
                access_token,
                TELLER_DOT_CERT,
                TELLER_DOT_KEY,
                TELLER_API_BASE_URL,
            )
            if updated:
                updated_accounts.append({"account_name": acc["name"]})

        db.session.commit()
        logger.debug(f"Balances refreshed for accounts: {updated_accounts}")
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Balances refreshed",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing balances: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_transactions.route("/update", methods=["PUT"])
def update_transaction():
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

        # Track changed fields
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
        if "merchant_typ" in data:
            txn.merchant_typ = data["merchant_typ"]
            changed_fields["merchant_typ"] = True

        # Mark user_modified
        txn.user_modified = True

        # Merge changes into user_modified_fields (which is a JSON dict)
        existing_fields = {}
        if txn.user_modified_fields:
            existing_fields = json.loads(txn.user_modified_fields)
        for field in changed_fields:
            existing_fields[field] = True
        txn.user_modified_fields = json.dumps(existing_fields)

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(...)
        return jsonify({"status": "error", "message": str(e)}), 500
