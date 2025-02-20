import json

import requests
from app.config import FILES, TELLER_APP_ID, logger
from app.extensions import db
from app.models import Account
from app.sql import account_logic
from app.sql.account_logic import get_accounts_from_db

from flask import Blueprint, jsonify, request

TELLER_DOT_KEY = FILES["TELLER_DOT_KEY"]
TELLER_DOT_CERT = FILES["TELLER_DOT_CERT"]
TELLER_TOKENS = FILES["TELLER_TOKENS"]
TELLER_ACCOUNTS = FILES["TELLER_ACCOUNTS"]
TELLER_API_BASE_URL = "https://api.teller.io"

link_teller = Blueprint("link_teller", __name__)
main_teller = Blueprint("main_teller", __name__)
transactions_bp = Blueprint("transactions", __name__)


def load_tokens():
    try:
        with open(TELLER_TOKENS, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding tokens: {e}")
        return []


def save_tokens(tokens):
    with open(TELLER_TOKENS, "w") as f:
        json.dump(tokens, f, indent=4)


def extract_accounts(data):
    if isinstance(data, dict) and "accounts" in data:
        return data["accounts"]
    return data


@link_teller.route("/generate_link_token", methods=["POST"])
def generate_link_token():
    try:
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
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.error(f"Error generating link token: {resp.json()}")
            return (
                jsonify({"status": "error", "message": resp.json()}),
                resp.status_code,
            )
        link_token = resp.json().get("link_token")
        return jsonify({"status": "success", "link_token": link_token}), 200
    except Exception as e:
        logger.error(f"Unexpected error generating link token: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@link_teller.route("/get_initial_info", methods=["GET"])
def get_item_details():
    try:
        tokens = load_tokens()
        if not tokens:
            return (
                jsonify({"status": "error", "message": "No access tokens found"}),
                400,
            )
        access_token = tokens[0].get("access_token")
        if not access_token:
            return jsonify({"status": "error", "message": "Invalid access token"}), 400
        url = f"{TELLER_API_BASE_URL}/accounts"
        resp = requests.get(
            url, cert=(TELLER_DOT_CERT, TELLER_DOT_KEY), auth=(access_token, "")
        )
        if resp.status_code != 200:
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
        accounts_data = extract_accounts(data)
        with open(TELLER_ACCOUNTS, "w") as f:
            json.dump(accounts_data, f, indent=4)
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
        logger.error(f"Error in get_initial_info: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@link_teller.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        accounts = get_accounts_from_db()  # use our helper
        logger.debug(f"Returning {len(accounts)} accounts from DB.")
        return jsonify({"status": "success", "data": {"accounts": accounts}}), 200
    except Exception as e:
        logger.error(f"Error fetching accounts from DB: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/exchange_public_token", methods=["POST"])
def exchange_public_token():
    try:
        data = request.json
        public_token = data.get("public_token")
        if not public_token:
            return jsonify({"error": "Missing public token"}), 400
        url = f"{TELLER_API_BASE_URL}/link_tokens/exchange"
        headers = {"Authorization": f"Bearer {TELLER_DOT_KEY}"}
        payload = {"public_token": public_token}
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            return jsonify({"error": resp.json()}), resp.status_code
        access_token = resp.json().get("access_token")
        user_id = resp.json().get("user", {}).get("id")
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
        logger.error(f"Error exchanging public token: {e}")
        return jsonify({"error": str(e)}), 500


@main_teller.route("/link_account", methods=["POST"])
def link_account():
    try:
        data = request.json
        public_token = data.get("public_token")
        if not public_token:
            return jsonify({"status": "error", "message": "Missing public token"}), 400
        url_exchange = f"{TELLER_API_BASE_URL}/link_tokens/exchange"
        headers = {"Authorization": f"Bearer {TELLER_DOT_KEY}"}
        payload = {"public_token": public_token}
        resp_exchange = requests.post(url_exchange, headers=headers, json=payload)
        if resp_exchange.status_code != 200:
            return (
                jsonify({"status": "error", "message": resp_exchange.json()}),
                resp_exchange.status_code,
            )
        access_token = resp_exchange.json().get("access_token")
        user_id = resp_exchange.json().get("user", {}).get("id")
        tokens = load_tokens()
        tokens.append({"user_id": user_id, "access_token": access_token})
        save_tokens(tokens)
        url_accounts = f"{TELLER_API_BASE_URL}/accounts"
        resp_accounts = requests.get(
            url_accounts,
            cert=(TELLER_DOT_CERT, TELLER_DOT_KEY),
            auth=(access_token, ""),
        )
        if resp_accounts.status_code != 200:
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
        accounts_data = extract_accounts(data_resp)
        account_logic.upsert_accounts(user_id, accounts_data)
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
        logger.error(f"Error linking account: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/refresh_accounts", methods=["POST"])
def refresh_accounts():
    try:
        accounts = Account.query.all()
        updated_accounts = []
        tokens = load_tokens()
        for account in accounts:
            access_token = None
            for token in tokens:
                if token.get("user_id") == account.user_id:
                    access_token = token.get("access_token")
                    break
            if not access_token:
                continue
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
        logger.error(f"Error refreshing account data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@transactions_bp.route("/get_transactions", methods=["GET"])
def get_transactions():
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
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/logs", methods=["GET"])
def get_logs():
    try:
        with open("logs/tokens.json", "r") as f:
            logs = [json.loads(line.strip()) for line in f]
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
