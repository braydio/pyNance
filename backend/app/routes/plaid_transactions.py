# File: app/routes/plaid_transactions.py
from datetime import datetime

from app.config import PLAID_BASE_URL, PLAID_CLIENT_ID, PLAID_CLIENT_NAME, logger
from app.extensions import db
from app.helpers.plaid_helpers import (
    exchange_public_token,
    generate_link_token,
    get_accounts,
    get_institution_name,
    get_item,
)
from app.models import Account
from app.sql import account_logic  # for upserting accounts and processing transactions
from flask import Blueprint, jsonify, request

plaid_transactions = Blueprint("plaid_transactions", __name__)


@plaid_transactions.route("/generate_link_token", methods=["POST"])
def generate_link_token_endpoint():
    data = request.get_json()
    user_id = data.get("user_id", PLAID_CLIENT_ID)
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
    user_id = data.get("user_id", "")
    public_token = data.get("public_token")
    if not user_id or not public_token:
        return jsonify({"error": "Missing user_id or public_token"}), 400

    try:
        # Step 1: Exchange token
        exchange_resp = exchange_public_token(public_token)
        if not exchange_resp:
            return jsonify({"error": "Token exchange failed"}), 500

        access_token = exchange_resp.get("access_token")
        item_id = exchange_resp.get("item_id")
        if not access_token or not item_id:
            return jsonify({"error": "Failed to exchange public token"}), 500

        # Step 2: Fetch item info to get institution_id
        item_info = get_item(access_token)
        institution_id = item_info.get("institution_id", "Unknown")
        institution_name = get_institution_name(institution_id)
        # Step 3: Fetch accounts
        accounts = get_accounts(access_token)

        # Step 4: Transform and upsert accounts
        transformed = []
        for acct in accounts:
            transformed.append(
                {
                    "id": acct.get("account_id"),
                    "name": acct.get("name")
                    or acct.get("official_name", "Unnamed Account"),
                    "type": str(acct.get("type") or "Unknown"),
                    "subtype": str(acct.get("subtype") or "Unknown"),
                    "balance": {"current": acct.get("balances", {}).get("current", 0)},
                    "status": "active",
                    "institution": {
                        "name": institution_name
                    },  # You can replace with institution name if desired
                    "access_token": access_token,
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
                    "institution_name": institution_id,  # Rename if you want to fetch/display full name later
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
    Expects JSON payload with "user_id" (optional, defaults to "").
    """
    try:
        logger.debug("Refreshing Plaid accounts from database.")
        user_id = request.get_json().get(PLAID_CLIENT_NAME, "Brayden")
        # Query only accounts for the given user that are linked via Plaid.
        accounts = Account.query.filter_by(
            user_id=PLAID_CLIENT_NAME, link_type="Plaid"
        ).all()
        if not accounts:
            logger.warning(f"No Plaid-linked accounts found for user {user_id}")
        updated_accounts = []

        for account in accounts:
            access_token = (
                account.access_token
            )  # Access token stored in the Account record
            if not access_token:
                logger.warning(
                    f"No Plaid access token found for account {account.account_id} (user {account.user_id})"
                )
                continue

            logger.debug(
                f"Refreshing Plaid account {account.account_id} using token: {access_token}"
            )
            updated = account_logic.refresh_data_for_plaid_account(
                access_token, PLAID_BASE_URL
            )
            if updated:
                updated_accounts.append(account.name)
                logger.debug(f"Balance updated as {account.balance}")
                account.last_refreshed = datetime.utcnow()
        db.session.commit()
        logger.debug(f"Refresh complete. Updated accounts: {updated_accounts}")
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


@plaid_transactions.route("/delete_account", methods=["DELETE"])
def delete_plaid_account():
    try:
        data = request.json
        account_id = data.get("account_id")
        if not account_id:
            return jsonify({"status": "error", "message": "Missing account_id"}), 400

        # Delete the account; cascading will remove related records.
        Account.query.filter_by(account_id=account_id).delete()
        db.session.commit()
        logger.info(
            f"Deleted Plaid account {account_id} and all related records via cascade."
        )
        return (
            jsonify(
                {"status": "success", "message": "Account and related records deleted"}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error deleting Plaid account: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
