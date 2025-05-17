# file: app/routes/plaid_transactions.py
from datetime import datetime

from app.config import PLAID_BASE_URL, PLAID_CLIENT_ID, PLAID_CLIENT_NAME, logger
from app.extensions import db
from app.helpers.plaid_helpers import (
    refresh_plaid_categories,
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
        logger.debug(
            f"Request to generate link token with user_id={user_id}, products={products}"
        )
        token = generate_link_token(products=products, user_id=user_id)
        if not token:
            logger.warning("Failed to generate link token - token was None")
            return (
                jsonify(
                    {"status": "error", "message": "Failed to generate link token"}
                ),
                500,
            )
        logger.info(f"Generated link token for user_id={user_id}")
        return jsonify({"status": "success", "link_token": token}), 200
    except Exception as e:
        logger.error(f"Error generating link token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_transactions.route("/exchange_public_token", methods=["POST"])
def exchange_public_token_endpoint():
    data = request.get_json()
    user_id = data.get("user_id", "")
    public_token = data.get("public_token")
    logger.debug(f"Received token exchange request for user_id={user_id}")

    if not user_id or not public_token:
        logger.warning("Missing user_id or public_token in request")
        return jsonify({"error": "Missing user_id or public_token"}), 400

    try:
        exchange_resp = exchange_public_token(public_token)
        logger.debug(f"Exchange response: {exchange_resp}")
        if not exchange_resp:
            logger.warning("Exchange returned no response")
            return jsonify({"error": "Token exchange failed"}), 500

        access_token = exchange_resp.get("access_token")
        item_id = exchange_resp.get("item_id")
        logger.info(
            f"Token exchange successful. Access Token: {access_token}, Item ID: {item_id}"
        )

        if not access_token or not item_id:
            logger.error("Missing access_token or item_id after exchange")
            return jsonify({"error": "Failed to exchange public token"}), 500

        item_info = get_item(access_token)
        institution_id = item_info.get("institution_id", "Unknown")
        institution_name = get_institution_name(institution_id)
        logger.debug(f"Institution ID: {institution_id}, Name: {institution_name}")

        accounts = get_accounts(access_token)
        logger.debug(f"Retrieved {len(accounts)} accounts from Plaid")

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
                    "institution": {"name": institution_name},
                    "access_token": access_token,
                    "enrollment_id": "",
                    "links": {},
                    "provider": "Plaid",
                }
            )

        account_logic.upsert_accounts(user_id, transformed, provider="Plaid")
        logger.info(f"Upserted {len(transformed)} accounts for user {user_id}")

        return (
            jsonify(
                {
                    "status": "success",
                    "item_id": item_id,
                    "institution_name": institution_id,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error exchanging public token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_transactions.route("/refresh_accounts", methods=["POST"])
def refresh_plaid_accounts():
    try:
        logger.debug("Starting refresh of Plaid accounts and Plaid Categories.")
        category_refresh = refresh_plaid_categories()
        if category_refresh:
            logger.info("Successfully refreshed Plaid categories.")
        user_id = request.get_json().get(PLAID_CLIENT_NAME, "Brayden")
        accounts = Account.query.filter_by(
            user_id=PLAID_CLIENT_NAME, link_type="Plaid"
        ).all()
        logger.debug(f"Found {len(accounts)} accounts for user_id={user_id}")

        if not accounts:
            logger.warning(f"No Plaid-linked accounts found for user {user_id}")
            return jsonify(
                {
                    "status": "success",
                    "message": "No linked Plaid accounts to refresh.",
                    "updated_accounts": [],
                }
            ), 200

        updated_accounts = []  # ✅ Fix: initialize variable

        for account in accounts:
            access_token = (
                account.plaid_account.access_token if account.plaid_account else None
            )
            if not access_token:
                logger.warning(
                    f"Missing access token for account {account.account_id} (user {account.user_id})"
                )
                continue

            logger.debug(
                f"Refreshing account {account.account_id} with token {access_token}"
            )
            plaid_accounts = get_accounts(access_token, user_id)
            for acct in plaid_accounts:
                account_id = acct.get("account_id")
                updated = account_logic.refresh_data_for_plaid_account(
                    access_token, account_id
                )

                if updated:
                    updated_accounts.append(account.name)
                    logger.debug(
                        f"Updated account: {account.name} with new balance {account.balance}"
                    )
                    account.last_refreshed = datetime.utcnow()

        db.session.commit()
        logger.info(f"Refreshed accounts: {updated_accounts}")

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
        logger.debug(f"Received request to delete account_id={account_id}")

        if not account_id:
            logger.warning("No account_id provided in request")
            return jsonify({"status": "error", "message": "Missing account_id"}), 400

        Account.query.filter_by(account_id=account_id).delete()
        db.session.commit()
        logger.info(f"Deleted Plaid account {account_id} and associated records")

        return (
            jsonify(
                {"status": "success", "message": "Account and related records deleted"}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error deleting Plaid account: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
