"""Routes for Teller account linking and data ingestion."""

import json

import requests
from datetime import datetime

from app.config import FILES, TELLER_APP_ID, logger
from app.helpers.teller_helpers import load_tokens, save_tokens
from flask import Blueprint, jsonify, request, session
from app.extensions import db
from app.models import TellerAccount
from app.sql import account_logic

# File paths and API endpoints
TELLER_DOT_KEY = FILES["TELLER_DOT_KEY"]
TELLER_DOT_CERT = FILES["TELLER_DOT_CERT"]
TELLER_ACCOUNTS = FILES["TELLER_ACCOUNTS"]
TELLER_API_BASE_URL = "https://api.teller.io"

link_teller = Blueprint("link_teller", __name__)
main_teller = Blueprint("main_teller", __name__)
transactions_bp = Blueprint("transactions", __name__)


def extract_accounts(data):
    logger.debug(f"Extracting accounts from data: {data}")
    if isinstance(data, dict) and "accounts" in data:
        return data["accounts"]
    logger.debug("Data does not contain an 'accounts' key; returning raw data.")
    return data


@link_teller.route("/link-token", methods=["POST"])
def generate_link_token():
    """Generate a Teller link token for the provided ``user_id``."""
    try:
        logger.debug("Generating Teller link token.")
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id") or session.get("user_id")
        if not user_id:
            logger.warning("Missing user_id in request body or session")
            return (
                jsonify({"status": "error", "message": "user_id is required"}),
                400,
            )

        url = f"{TELLER_API_BASE_URL}/link_tokens"
        headers = {
            "Authorization": f"Bearer {TELLER_DOT_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "application_id": TELLER_APP_ID,
            "user_id": user_id,
            "products": ["transactions", "balance"],
        }
        logger.debug(f"POST {url} with headers={headers} and payload={payload}")
        resp = requests.post(url, headers=headers, json=payload)
        logger.debug(f"Response status: {resp.status_code}, body: {resp.text}")
        if resp.status_code != 200:
            logger.error(f"Error generating link token: {resp.json()}")
            return (
                jsonify({"status": "error", "message": resp.json()}),
                resp.status_code,
            )
        link_token = resp.json().get("link_token")
        logger.debug(f"Generated link token: {link_token}")
        return jsonify({"status": "success", "link_token": link_token}), 200
    except Exception as e:
        logger.error(f"Unexpected error generating link token: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@link_teller.route("/link", methods=["POST"])
def link_account():
    """Persist a Teller access token and ingest account metadata."""
    data = request.get_json(silent=True) or {}
    access_token = data.get("access_token")
    user_id = data.get("user_id") or session.get("user_id")
    if not access_token or not user_id:
        return (
            jsonify(
                {"status": "error", "message": "access_token and user_id required"}
            ),
            400,
        )

    tokens = load_tokens()
    tokens.append({"user_id": user_id, "access_token": access_token})
    save_tokens(tokens)

    url = f"{TELLER_API_BASE_URL}/accounts"
    resp = requests.get(
        url, cert=(TELLER_DOT_CERT, TELLER_DOT_KEY), auth=(access_token, "")
    )
    if resp.status_code != 200:
        logger.error("Failed to fetch accounts during link: %s", resp.text)
        return (
            jsonify({"status": "error", "message": "Failed to fetch accounts"}),
            resp.status_code,
        )

    accounts_data = extract_accounts(resp.json())
    account_logic.upsert_accounts(
        user_id, accounts_data, provider="Teller", access_token=access_token
    )

    for acct in accounts_data:
        acct_id = acct.get("id") or acct.get("account_id")
        if not acct_id:
            continue
        rec = TellerAccount.query.filter_by(account_id=acct_id).first()
        if rec:
            rec.access_token = access_token
            rec.updated_at = datetime.utcnow()
        else:
            db.session.add(TellerAccount(account_id=acct_id, access_token=access_token))

    db.session.commit()

    return (
        jsonify({"status": "success", "accounts_linked": len(accounts_data)}),
        200,
    )


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
        logger.debug(f"Response status: {resp.status_code}, body: {resp.text}")
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
        accounts_data = extract_accounts(data)
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


@link_teller.route("/accounts", methods=["GET"])
def get_accounts():
    try:
        logger.debug("Fetching accounts from the database.")
        from app.sql.account_logic import get_accounts_from_db

        accounts = get_accounts_from_db()
        logger.debug(f"Fetched {len(accounts)} accounts from DB.")
        return jsonify({"status": "success", "data": {"accounts": accounts}}), 200
    except Exception as e:
        logger.error(f"Error fetching accounts from DB: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@link_teller.route("/balances", methods=["GET"])
def get_balances():
    """Return a mapping of account_id to current balance."""
    try:
        accounts = account_logic.get_accounts_from_db(include_hidden=True)
        balances = {
            acc["account_id"]: {"available": acc["balance"]} for acc in accounts
        }
        return jsonify({"status": "success", "balances": balances}), 200
    except Exception as e:
        logger.error("Error fetching balances: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
