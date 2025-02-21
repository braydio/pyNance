import json

import requests
from app.config import FILES, TELLER_APP_ID, logger
from app.extensions import db
from app.models import Account, Transaction
from app.sql import account_logic
from app.sql.account_logic import get_accounts_from_db

from flask import Blueprint, jsonify, request

# Define file paths and API endpoints
TELLER_DOT_KEY = FILES["TELLER_DOT_KEY"]
TELLER_DOT_CERT = FILES["TELLER_DOT_CERT"]
TELLER_TOKENS = FILES["TELLER_TOKENS"]
TELLER_ACCOUNTS = FILES["TELLER_ACCOUNTS"]
TELLER_API_BASE_URL = "https://api.teller.io"

# Define Blueprints
link_teller = Blueprint("link_teller", __name__)
main_teller = Blueprint("main_teller", __name__)
transactions_bp = Blueprint("transactions", __name__)


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


def extract_accounts(data):
    logger.debug(f"Extracting accounts from data: {data}")
    if isinstance(data, dict) and "accounts" in data:
        accounts = data["accounts"]
        logger.debug(f"Extracted accounts: {accounts}")
        return accounts
    logger.debug("Data does not contain an 'accounts' key; returning raw data.")
    return data


@link_teller.route("/generate_link_token", methods=["POST"])
def generate_link_token():
    try:
        logger.debug("Generating Teller link token.")
        url = f"{TELLER_API_BASE_URL}/link_tokens"
        headers = {
            "Authorization": f"Bearer {TELLER_DOT_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "application_id": TELLER_APP_ID,
            "user_id": "user_12345",
            "products": ["transactions", "balance"],
        }
        logger.debug(f"POST {url} with headers={headers} and payload={payload}")
        resp = requests.post(url, headers=headers, json=payload)
        logger.debug(f"Response status: {resp.status_code}, response body: {resp.text}")
        if resp.status_code != 200:
            logger.error(f"Error generating link token: {resp.json()}")
            return (
                jsonify({"status": "error", "message": resp.json()}),
                resp.status_code,
            )
        link_token = resp.json().get("link_token")
        logger.debug(f"Successfully generated link token: {link_token}")
        return jsonify({"status": "success", "link_token": link_token}), 200
    except Exception as e:
        logger.error(f"Unexpected error generating link token: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@link_teller.route("/get_initial_info", methods=["GET"])
def get_item_details():
    try:
        logger.debug("Fetching initial account information.")
        tokens = load_tokens()
        if not tokens:
            logger.warning("No access tokens found.")
            return (
                jsonify({"status": "error", "message": "No access tokens found"}),
                400,
            )

        access_token = tokens[0].get("access_token")
        logger.debug(f"Using access token: {access_token}")
        if not access_token:
            logger.error("Access token is invalid or missing.")
            return jsonify({"status": "error", "message": "Invalid access token"}), 400

        url = f"{TELLER_API_BASE_URL}/accounts"
        logger.debug(
            f"GET {url} with cert=({TELLER_DOT_CERT}, {TELLER_DOT_KEY}) and auth=({access_token}, '')"
        )
        resp = requests.get(
            url, cert=(TELLER_DOT_CERT, TELLER_DOT_KEY), auth=(access_token, "")
        )
        logger.debug(f"Response status: {resp.status_code}, response body: {resp.text}")
        if resp.status_code != 200:
            logger.error(f"Failed to fetch accounts: {resp.text}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to fetch accounts: {resp.text}",
                    }
                ),
                resp.status_code,
            )

        data = resp.json()
        logger.debug(f"Raw data received: {data}")
        accounts_data = extract_accounts(data)
        logger.debug(f"Extracted accounts data: {accounts_data}")
        with open(TELLER_ACCOUNTS, "w") as f:
            json.dump(accounts_data, f, indent=4)
        logger.debug(f"Accounts data saved to {TELLER_ACCOUNTS}")
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Accounts fetched successfully",
                    "data": accounts_data,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error in get_initial_info: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@link_teller.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        logger.debug("Fetching accounts from the database.")
        accounts = get_accounts_from_db()  # use our helper
        logger.debug(f"Fetched {len(accounts)} accounts from DB.")
        return jsonify({"status": "success", "data": {"accounts": accounts}}), 200
    except Exception as e:
        logger.error(f"Error fetching accounts from DB: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/exchange_public_token", methods=["POST"])
def exchange_public_token():
    try:
        logger.debug("Exchanging public token for access token.")
        data = request.json
        logger.debug(f"Request JSON: {data}")
        public_token = data.get("public_token")
        if not public_token:
            logger.error("Missing public token in request.")
            return jsonify({"error": "Missing public token"}), 400

        url = f"{TELLER_API_BASE_URL}/link_tokens/exchange"
        headers = {"Authorization": f"Bearer {TELLER_DOT_KEY}"}
        payload = {"public_token": public_token}
        logger.debug(f"POST {url} with headers={headers} and payload={payload}")
        resp = requests.post(url, headers=headers, json=payload)
        logger.debug(f"Response status: {resp.status_code}, response body: {resp.text}")
        if resp.status_code != 200:
            logger.error(f"Error exchanging public token: {resp.json()}")
            return jsonify({"error": resp.json()}), resp.status_code

        access_token = resp.json().get("access_token")
        user_id = resp.json().get("user", {}).get("id")
        logger.debug(
            f"Exchange successful: access_token={access_token}, user_id={user_id}"
        )
        tokens = load_tokens()
        tokens.append({"user_id": user_id, "access_token": access_token})
        save_tokens(tokens)
        return (
            jsonify(
                {"status": "success", "access_token": access_token, "user_id": user_id}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error exchanging public token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@main_teller.route("/link_account", methods=["POST"])
def link_account():
    try:
        logger.debug("Linking account with public token.")
        data = request.json
        logger.debug(f"Request JSON: {data}")
        public_token = data.get("public_token")
        if not public_token:
            logger.error("Missing public token in link_account request.")
            return jsonify({"status": "error", "message": "Missing public token"}), 400

        url_exchange = f"{TELLER_API_BASE_URL}/link_tokens/exchange"
        headers = {"Authorization": f"Bearer {TELLER_DOT_KEY}"}
        payload = {"public_token": public_token}
        logger.debug(
            f"Exchanging public token: POST {url_exchange} with payload={payload}"
        )
        resp_exchange = requests.post(url_exchange, headers=headers, json=payload)
        logger.debug(
            f"Exchange response status: {resp_exchange.status_code}, body: {resp_exchange.text}"
        )
        if resp_exchange.status_code != 200:
            logger.error(f"Exchange failed: {resp_exchange.json()}")
            return (
                jsonify({"status": "error", "message": resp_exchange.json()}),
                resp_exchange.status_code,
            )

        access_token = resp_exchange.json().get("access_token")
        user_id = resp_exchange.json().get("user", {}).get("id")
        logger.debug(
            f"Exchange successful: access_token={access_token}, user_id={user_id}"
        )
        tokens = load_tokens()
        tokens.append({"user_id": user_id, "access_token": access_token})
        save_tokens(tokens)

        url_accounts = f"{TELLER_API_BASE_URL}/accounts"
        logger.debug(
            f"Fetching accounts: GET {url_accounts} with cert=({TELLER_DOT_CERT}, {TELLER_DOT_KEY}) and auth=({access_token}, '')"
        )
        resp_accounts = requests.get(
            url_accounts,
            cert=(TELLER_DOT_CERT, TELLER_DOT_KEY),
            auth=(access_token, ""),
        )
        logger.debug(
            f"Accounts response status: {resp_accounts.status_code}, body: {resp_accounts.text}"
        )
        if resp_accounts.status_code != 200:
            logger.error(f"Failed to fetch accounts: {resp_accounts.text}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to fetch accounts: {resp_accounts.text}",
                    }
                ),
                resp_accounts.status_code,
            )

        data_resp = resp_accounts.json()
        logger.debug(f"Accounts response JSON: {data_resp}")
        accounts_data = extract_accounts(data_resp)
        logger.debug(f"Extracted accounts data: {accounts_data}")
        account_logic.upsert_accounts(user_id, accounts_data)
        logger.debug("Account linking and saving completed successfully.")
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Account linked and saved",
                    "data": accounts_data,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error linking account: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/refresh_accounts", methods=["POST"])
def refresh_accounts():
    try:
        logger.debug("Refreshing accounts from the database.")
        accounts = Account.query.all()
        logger.debug(f"Found {len(accounts)} accounts to refresh.")
        updated_accounts = []
        tokens = load_tokens()
        logger.debug(f"Loaded tokens: {tokens}")
        for account in accounts:
            access_token = None
            for token in tokens:
                if token.get("user_id") == account.user_id:
                    access_token = token.get("access_token")
                    logger.debug(
                        f"Found access token for user_id {account.user_id}: {access_token}"
                    )
                    break
            if not access_token:
                logger.warning(
                    f"No access token found for account user_id: {account.user_id}"
                )
                continue
            logger.debug(
                f"Refreshing account {account.account_id} using access token: {access_token}"
            )
            updated = account_logic.refresh_account_data_for_account(
                account,
                access_token,
                TELLER_DOT_CERT,
                TELLER_DOT_KEY,
                TELLER_API_BASE_URL,
            )
            if updated:
                logger.debug(f"Account {account.account_id} was updated.")
                updated_accounts.append(account.account_id)
            else:
                logger.debug(f"Account {account.account_id} did not require an update.")
        db.session.commit()
        logger.debug(
            f"Database commit successful. Updated accounts: {updated_accounts}"
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Account data refreshed",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing account data: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/refresh_balances", methods=["POST"])
def refresh_balances():
    """
    For each account in the database, this endpoint calls the Teller API
    to fetch the latest balances (using the -u style authentication) and then
    updates the historical balances (AccountHistory) in the DB.
    """
    try:
        accounts = Account.query.all()
        updated_accounts = []
        tokens = load_tokens()  # Assumes tokens are stored and retrievable

        for account in accounts:
            # Find the access token for the account's user.
            access_token = None
            for token in tokens:
                if token.get("user_id") == account.user_id:
                    access_token = token.get("access_token")
                    break

            if not access_token:
                logger.warning(
                    f"No access token found for account {account.account_id}"
                )
                continue

            # Use our existing refresh logic to fetch balances & update history.
            updated = account_logic.refresh_account_data_for_account(
                account,
                access_token,
                TELLER_DOT_CERT,
                TELLER_DOT_KEY,
                TELLER_API_BASE_URL,
            )
            if updated:
                updated_accounts.append(account.account_id)

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


@transactions_bp.route("/get_transactions", methods=["GET"])
def get_transactions():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))
        logger.debug(
            f"Fetching transactions for page {page} with page_size {page_size}"
        )
        transactions_list, total = account_logic.get_paginated_transactions(
            page, page_size
        )
        logger.debug(
            f"Retrieved {len(transactions_list)} transactions out of {total} total."
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
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/update", methods=["PUT"])
def update_transaction():
    """
    Update a transaction's editable details based on user input.
    Expected JSON payload:
      {
         "transaction_id": "txn_123456",
         "amount": 123.45,
         "date": "2025-02-20",
         "description": "Updated description",
         "category": "Updated Category",
         "merchant_name": "Updated Merchant",
         "merchant_typ": "Updated Type"
      }
    Only these fields will be updated; transaction_id (and account_id) are not modified.
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

        # Update only the allowed fields if they are provided.
        if "amount" in data:
            txn.amount = float(data["amount"])
        if "date" in data:
            txn.date = data["date"]
        if "description" in data:
            txn.description = data["description"]
        if "category" in data:
            txn.category = data["category"]
        if "merchant_name" in data:
            txn.merchant_name = data["merchant_name"]
        if "merchant_typ" in data:
            txn.merchant_typ = data["merchant_typ"]

        db.session.commit()
        logger.debug(f"Transaction {transaction_id} updated with data: {data}")
        return (
            jsonify(
                {"status": "success", "message": "Transaction updated successfully."}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error updating transaction: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/logs", methods=["GET"])
def get_logs():
    try:
        logger.debug("Attempting to read logs from logs/tokens.json")
        with open("logs/tokens.json", "r") as f:
            logs = [json.loads(line.strip()) for line in f]
        logger.debug(f"Successfully read {len(logs)} log entries.")
        return jsonify({"logs": logs})
    except Exception as e:
        logger.error(f"Error reading logs: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
