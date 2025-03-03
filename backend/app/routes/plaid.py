# File: app/routes/plaid.py

import json

import requests
from app.config import (
    FILES,
    PLAID_BASE_URL,
    PLAID_CLIENT_ID,
    PLAID_SECRET,
    PRODUCTS,
    logger,
)
from app.sql import account_logic

from flask import Blueprint, jsonify, request

plaid_bp = Blueprint("plaid", __name__)


def transform_plaid_account(plaid_account):
    """
    Transform a Plaid account object into the format expected by the
    upsert_accounts method. Adjust keys as needed.
    """
    transformed = {
        "id": plaid_account.get("account_id"),
        "name": plaid_account.get("name")
        or plaid_account.get("official_name", "Unnamed Account"),
        "type": plaid_account.get("type") or "Unknown",
        "subtype": plaid_account.get("subtype") or "Unknown",
        # Plaid returns a nested "balances" object; we extract "current".
        "balance": {"current": plaid_account.get("balances", {}).get("current", 0)},
        "status": "active",  # Plaid does not provide a status; default to active.
        "institution": {"name": plaid_account.get("institution_name", "Unknown")},
        "enrollment_id": "",  # Not applicable for Plaid; leave empty.
        "links": {},  # Not applicable; can be populated if needed.
    }
    return transformed


@plaid_bp.route("/generate_link_token", methods=["POST"])
def generate_link_token():
    """
    Create a Plaid link token by calling Plaid's /link/token/create endpoint.
    The request body should include a JSON object with at least a "user_id".
    """
    try:
        # Build the payload for link token creation.
        user_id = request.json.get("user_id", "default_user")
        payload = {
            "client_id": PLAID_CLIENT_ID,
            "secret": PLAID_SECRET,
            "client_name": "pyNance",
            "products": PRODUCTS,  # e.g. ["transactions"]
            "country_codes": ["US"],
            "language": "en",
            "user": {"client_user_id": user_id},
        }
        url = f"{PLAID_BASE_URL}/link/token/create"
        logger.debug(f"Plaid generate_link_token: POST {url} with payload: {payload}")
        resp = requests.post(url, json=payload)
        if resp.status_code != 200:
            logger.error(f"Error generating Plaid link token: {resp.text}")
            return jsonify({"status": "error", "message": resp.text}), resp.status_code
        link_token = resp.json().get("link_token")
        logger.debug(f"Plaid link token generated: {link_token}")
        return jsonify({"status": "success", "link_token": link_token}), 200
    except Exception as e:
        logger.error(
            f"Unexpected error generating Plaid link token: {e}", exc_info=True
        )
        return jsonify({"status": "error", "message": str(e)}), 500


@plaid_bp.route("/exchange_public_token", methods=["POST"])
def exchange_public_token():
    """
    Exchange the public token (received from the Plaid Link flow)
    for an access token. Expects a JSON payload with a "public_token" (and optionally a "user_id").
    """
    try:
        data = request.json
        public_token = data.get("public_token")
        if not public_token:
            return jsonify({"status": "error", "message": "Missing public token"}), 400

        payload = {
            "client_id": PLAID_CLIENT_ID,
            "secret": PLAID_SECRET,
            "public_token": public_token,
        }
        url = f"{PLAID_BASE_URL}/item/public_token/exchange"
        logger.debug(f"Plaid exchange_public_token: POST {url} with payload: {payload}")
        resp = requests.post(url, json=payload)
        if resp.status_code != 200:
            logger.error(f"Error exchanging Plaid public token: {resp.text}")
            return jsonify({"status": "error", "message": resp.text}), resp.status_code

        exchange_data = resp.json()
        access_token = exchange_data.get("access_token")
        item_id = exchange_data.get("item_id")
        user_id = data.get("user_id", "default_user")

        # For demonstration, we store the Plaid token in the same file used for Teller tokens.
        # In a production app, consider using a dedicated database table for tokens.
        tokens_file = FILES.get("PLAID_TOKENS", FILES["TELLER_TOKENS"])
        try:
            with open(tokens_file, "r") as f:
                tokens = json.load(f)
        except Exception:
            tokens = []
        tokens.append(
            {"user_id": user_id, "item_id": item_id, "access_token": access_token}
        )
        with open(tokens_file, "w") as f:
            json.dump(tokens, f, indent=4)
        logger.debug(f"Plaid token exchange successful: {exchange_data}")
        return (
            jsonify(
                {"status": "success", "access_token": access_token, "item_id": item_id}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error exchanging Plaid public token: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@plaid_bp.route("/get_accounts", methods=["GET"])
def get_accounts():
    """
    Fetch accounts from Plaid using the stored access token.
    This endpoint calls Plaid's /accounts/get endpoint and then transforms
    the accounts data into the format expected by the upsert_accounts method.
    """
    try:
        # For simplicity, we retrieve the first Plaid token.
        tokens_file = FILES.get("PLAID_TOKENS", FILES["TELLER_TOKENS"])
        try:
            with open(tokens_file, "r") as f:
                tokens = json.load(f)
        except Exception:
            tokens = []
        if not tokens:
            return jsonify({"status": "error", "message": "No Plaid tokens found"}), 400

        token = tokens[0]
        access_token = token.get("access_token")
        user_id = token.get("user_id", "default_user")
        url = f"{PLAID_BASE_URL}/accounts/get"
        payload = {
            "client_id": PLAID_CLIENT_ID,
            "secret": PLAID_SECRET,
            "access_token": access_token,
        }
        logger.debug(f"Plaid get_accounts: POST {url} with payload: {payload}")
        resp = requests.post(url, json=payload)
        if resp.status_code != 200:
            logger.error(f"Error fetching Plaid accounts: {resp.text}")
            return jsonify({"status": "error", "message": resp.text}), resp.status_code

        accounts_data = resp.json().get("accounts", [])
        # Transform each Plaid account object to our expected format.
        transformed_accounts = [transform_plaid_account(acc) for acc in accounts_data]
        # Use your existing upsert logic to insert/update accounts in the DB.
        account_logic.upsert_accounts(user_id, transformed_accounts)
        logger.debug("Plaid accounts fetched and processed successfully.")
        return jsonify({"status": "success", "data": transformed_accounts}), 200
    except Exception as e:
        logger.error(f"Error fetching Plaid accounts: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@plaid_bp.route("/refresh_accounts", methods=["POST"])
def refresh_accounts():
    """
    For each stored Plaid token, fetch the latest accounts from Plaid
    and update the database.
    """
    try:
        logger.debug("Wrong modules. this is plaid.py")
        tokens_file = FILES.get("PLAID_TOKENS", FILES["TELLER_TOKENS"])
        try:
            with open(tokens_file, "r") as f:
                tokens = json.load(f)
        except Exception:
            tokens = []
        if not tokens:
            return jsonify({"status": "error", "message": "No Plaid tokens found"}), 400

        updated_items = []
        for token in tokens:
            access_token = token.get("access_token")
            user_id = token.get("user_id", "default_user")
            url = f"{PLAID_BASE_URL}/accounts/get"
            payload = {
                "client_id": PLAID_CLIENT_ID,
                "secret": PLAID_SECRET,
                "access_token": access_token,
            }
            logger.debug(f"Plaid refresh_accounts: POST {url} with payload: {payload}")
            resp = requests.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(f"Error refreshing Plaid accounts: {resp.text}")
                continue
            accounts_data = resp.json().get("accounts", [])
            transformed_accounts = [
                transform_plaid_account(acc) for acc in accounts_data
            ]
            account_logic.upsert_accounts(user_id, transformed_accounts)
            updated_items.append(token.get("item_id", "unknown"))
        return jsonify({"status": "success", "updated_items": updated_items}), 200
    except Exception as e:
        logger.error(f"Error refreshing Plaid accounts: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
