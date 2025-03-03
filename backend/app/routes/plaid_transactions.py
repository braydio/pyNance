# File: app/routes/plaid_transactions.py

from app.config import PLAID_BASE_URL, logger
from app.extensions import db
from app.helpers.plaid_helpers import (
    exchange_public_token,
    generate_link_token,
    get_accounts,
)
from app.models import Account
from app.sql import account_logic  # for upserting accounts and processing transactions

from flask import Blueprint, jsonify, request

plaid_transactions = Blueprint("plaid_transactions", __name__)


@plaid_transactions.route("/generate_link_token", methods=["POST"])
def generate_link_token_endpoint():
    """
    Generate a Plaid link token for the transactions product.
    Expects JSON payload with "user_id" and optionally "products".
    """
    data = request.get_json()
    user_id = data.get("user_id", "default_user")
    products = data.get("products", ["transactions"])
    try:
        token = generate_link_token(products=products, user_id=user_id)
        if not token:
            return (
                jsonify(
                    {"status": "error", "message": "Failed to generate link token"}
                ),
                500,
            )
        return jsonify({"status": "success", "link_token": token}), 200
    except Exception as e:
        logger.error(f"Error generating link token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_transactions.route("/exchange_public_token", methods=["POST"])
def exchange_public_token_endpoint():
    """
    Exchange the public token for an access token and save initial accounts.
    Expects JSON with "user_id" and "public_token".
    """
    data = request.get_json()
    user_id = data.get("user_id", "default_user")
    public_token = data.get("public_token")
    if not user_id or not public_token:
        return jsonify({"error": "Missing user_id or public_token"}), 400
    try:
        exchange_resp = exchange_public_token(public_token)
        if not exchange_resp:
            return jsonify({"error": "Token exchange failed"}), 500
        access_token = exchange_resp.get("access_token")
        item_id = exchange_resp.get("item_id")
        if not access_token or not item_id:
            return jsonify({"error": "Failed to exchange public token"}), 500

        # Fetch accounts to retrieve institution info using existing SQL logic.
        accounts_data = get_accounts(access_token)
        institution_name = accounts_data.get("item", {}).get(
            "institution_name", "Unknown"
        )
        # Save the token using your SQL logic.
        account_logic.save_plaid_item(
            user_id, item_id, access_token, institution_name, product="transactions"
        )
        # Transform and upsert accounts.
        transformed = []
        for acct in accounts_data.get("accounts", []):
            transformed.append(
                {
                    "id": acct.get("account_id"),
                    "name": acct.get("name")
                    or acct.get("official_name", "Unnamed Account"),
                    "type": acct.get("type") or "Unknown",
                    "subtype": acct.get("subtype") or "Unknown",
                    "balance": {"current": acct.get("balances", {}).get("current", 0)},
                    "status": "active",
                    "institution": {"name": institution_name},
                    "enrollment_id": "",
                    "links": {},
                    "provider": "Plaid",
                }
            )
        account_logic.upsert_accounts(user_id, transformed, provider="Plaid")
        return (
            jsonify(
                {
                    "status": "success",
                    "item_id": item_id,
                    "institution_name": institution_name,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error exchanging public token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_transactions.route("/refresh_accounts", methods=["POST"])
def refresh_plaid_accounts():
    """
    Refresh Plaid-linked accounts using tokens stored in the Accounts table.
    Expects JSON payload with "user_id" (optional, defaults to "default_user").
    """
    try:
        logger.debug("Refreshing Plaid accounts from database.")
        user_id = request.get_json().get("user_id", "default_user")
        # Query only accounts for the given user.
        accounts = Account.query.filter_by(user_id=user_id).all()
        updated_accounts = []

        for account in accounts:
            access_token = account.access_token  # Now stored in the Account record
            if not access_token:
                logger.warning(
                    f"No Plaid access token found for account {account.account_id} (user {account.user_id})"
                )
                continue
            logger.debug(
                f"Refreshing Plaid account {account.account_id} using token: {access_token}"
            )
            updated = account_logic.refresh_data_for_plaid_account(
                account, access_token, PLAID_BASE_URL
            )
            if updated:
                updated_accounts.append(
                    {"account_id": account.account_id, "account_name": account.name}
                )
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Plaid account data refreshed",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing Plaid accounts: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
