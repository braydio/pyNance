# app/routes/teller.py
import json

from app.config import FILES, logger
from app.helper_utils import load_json
from app.services.teller_helpers import (
    exchange_public_token as teller_exchange_public_token,
)
from app.services.teller_helpers import (
    generate_link_token as teller_generate_link_token,
)
from app.services.teller_helpers import initial_get_info
from app.services.teller_refresh_service import load_accounts, process_tokens

from flask import Blueprint, jsonify, request

teller_api = Blueprint("teller_api", __name__, url_prefix="/api/teller")


@teller_api.route("/generate_link_token", methods=["POST"])
def generate_link_token_endpoint():
    try:
        token = teller_generate_link_token()
        if not token:
            return (
                jsonify(
                    {"status": "error", "message": "Failed to generate link token"}
                ),
                500,
            )
        return jsonify({"status": "success", "link_token": token}), 200
    except Exception as e:
        logger.error(f"Error generating Teller link token: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_api.route("/exchange_public_token", methods=["POST"])
def exchange_public_token_endpoint():
    try:
        data = request.get_json() or {}
        public_token = data.get("public_token")
        if not public_token:
            return jsonify({"error": "Missing public token"}), 400
        access_token = teller_exchange_public_token(public_token)
        if not access_token:
            return jsonify({"error": "Exchange failed"}), 400
        user_id = data.get("user_id")
        tokens = load_json(FILES["TELLER_TOKENS"]) or {}
        tokens.setdefault("tokens", []).append(
            {"user_id": user_id, "access_token": access_token}
        )
        with open(FILES["TELLER_TOKENS"], "w") as f:
            json.dump(tokens, f, indent=4)
        accounts = initial_get_info(access_token)
        if accounts is None:
            return (
                jsonify({"status": "error", "message": "Failed to fetch accounts"}),
                500,
            )
        return (
            jsonify(
                {"status": "success", "access_token": access_token, "user_id": user_id}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error exchanging Teller public token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@teller_api.route("/save_token", methods=["POST"])
def save_token():
    """
    Save the access token and user ID from Teller Connect.
    """
    try:
        data = request.get_json()
        access_token = data.get("accessToken")
        user_id = data.get("user", {}).get("id")
        enrollment = data.get("enrollment", {}).get("id")
        institution = data.get("enrollment", {}).get("institution", {}).get("name")

        if not access_token or not user_id:
            return (
                jsonify(
                    {"status": "error", "message": "Missing access token or user ID"}
                ),
                400,
            )

        # Load existing tokens
        tokens = load_json(FILES["TELLER_TOKENS"]) or []

        # Add the new token
        tokens.append(
            {
                "user_id": user_id,
                "access_token": access_token,
                "enrollment_id": enrollment,
                "institution": institution,
            }
        )

        with open(FILES["TELLER_TOKENS"], "w") as f:
            json.dump(tokens, f, indent=4)

        return (
            jsonify({"status": "success", "message": "Token saved successfully"}),
            200,
        )

    except Exception as e:
        logger.error(f"Error saving token: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_api.route("/load_accounts", methods=["GET"])
def load_teller_accounts():
    try:
        with open(FILES["TELLER_ACCOUNTS"], "r") as f:
            accounts = json.load(f)
        return jsonify({"status": "success", "data": accounts}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


teller_refresh_api = Blueprint("teller_refresh_api", __name__, url_prefix="/api/teller")


@teller_refresh_api.route("/refresh_accounts", methods=["POST"])
def refresh_accounts():
    """
    Refresh all accounts by processing Teller tokens.
    """
    try:
        process_tokens()  # This will refresh all accounts
        return (
            jsonify(
                {"status": "success", "message": "Accounts refreshed successfully"}
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_refresh_api.route("/get_accounts", methods=["GET"])
def get_accounts():
    """
    Fetch the list of all processed accounts.
    """
    try:
        accounts_data = load_accounts(FILES["TELLER_ACCOUNTS"])
        return jsonify({"status": "success", "data": accounts_data["accounts"]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
