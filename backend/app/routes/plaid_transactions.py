from datetime import datetime, timedelta

from app.config import logger
from app.helpers.plaid_helpers import (
    exchange_public_token,
    generate_link_token,
    get_accounts,
    get_transactions,
)
from app.sql import account_logic  # existing module for upserting accounts

from flask import Blueprint, jsonify, request

plaid_transactions = Blueprint("plaid_transactions", __name__)


@plaid_transactions.route("/generate_link_token", methods=["POST"])
def generate_link_token_endpoint():
    """
    Generate a Plaid link token for the transactions product.
    Expects JSON payload with "user_id".
    """
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    try:
        token = generate_link_token(user_id, products=["transactions"])
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
    user_id = data.get("user_id")
    public_token = data.get("public_token")
    if not user_id or not public_token:
        return jsonify({"error": "Missing user_id or public_token"}), 400
    try:
        exchange_resp = exchange_public_token(public_token)
        access_token = exchange_resp.get("access_token")
        item_id = exchange_resp.get("item_id")
        if not access_token or not item_id:
            return jsonify({"error": "Failed to exchange public token"}), 500
        # Fetch accounts to retrieve institution info
        accounts_data = account_logic.get_accounts(access_token)
        institution_name = accounts_data.get("item", {}).get(
            "institution_name", "Unknown"
        )
        # Save the token in the DB (separate from Teller)
        account_logic.save_plaid_item(
            user_id, item_id, access_token, institution_name, product="transactions"
        )
        # Transform Plaid account data for upsert (note: adjust keys as needed)
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
                    "provider": "Plaid",  # mark this as Plaid-linked
                }
            )
        # Call your existing upsert function (ensure it accepts a provider parameter)
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
def refresh_accounts_endpoint():
    """
    Refresh linked transactions accounts and transactions.
    Expects JSON with "user_id" and "item_id".
    """
    data = request.get_json()
    user_id = data.get("user_id")
    item_id = data.get("item_id")
    if not user_id or not item_id:
        return jsonify({"error": "Missing user_id or item_id"}), 400
    try:
        # Retrieve the PlaidItem record (you could also query by item_id and user_id)
        from app.models import PlaidItem

        item = PlaidItem.query.filter_by(
            item_id=item_id, user_id=user_id, product="transactions"
        ).first()
        if not item:
            return jsonify({"error": "Plaid item not found"}), 404
        # Refresh accounts data
        accounts_data = get_accounts(item.access_token)
        institution_name = accounts_data.get("item", {}).get(
            "institution_name", "Unknown"
        )
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
        # Refresh transactions (for a default 30-day range)
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        tx_data = get_transactions(item.access_token, start_date, end_date)
        transactions = tx_data.get("transactions", [])
        # Call your transaction-processing logic (assumed to be similar to Teller's)
        account_logic.process_transactions(user_id, transactions, provider="Plaid")
        return (
            jsonify(
                {
                    "status": "success",
                    "accounts_refreshed": len(transformed),
                    "transactions_refreshed": len(transactions),
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing accounts: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
