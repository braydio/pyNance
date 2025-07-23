from app.config import logger
from app.helpers.plaid_helpers import (
    exchange_public_token,
    generate_link_token,
    get_accounts,
    get_investments,
)
from app.models import PlaidAccount
from app.sql.account_logic import save_plaid_account, upsert_accounts
from flask import Blueprint, jsonify, request

plaid_investments = Blueprint("plaid_investments", __name__)


@plaid_investments.route("/generate_link_token", methods=["POST"])
def generate_link_token_investments():
    """
    Generate a Plaid link token for the investments product.
    Expects JSON payload with "user_id".
    """
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    try:
        token = generate_link_token(user_id, products=["investments"])
        return jsonify({"status": "success", "link_token": token}), 200
    except Exception as e:
        logger.error(f"Error generating investments link token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_investments.route("/exchange_public_token", methods=["POST"])
def exchange_public_token_investments():
    """
    Exchange a public token for an access token for investments.
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
        accounts = get_accounts(access_token, user_id)
        upsert_accounts(user_id, accounts, provider="Plaid", access_token=access_token)
        for acct in accounts:
            acct_id = acct.get("account_id")
            if acct_id:
                save_plaid_account(acct_id, item_id, access_token, "investments")
        # Save initial investments data (if you have specific logic, call it here)
        # e.g., account_logic.save_investments_data(user_id, access_token)
        return (
            jsonify(
                {
                    "status": "success",
                    "item_id": item_id,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error exchanging investments public token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_investments.route("/refresh", methods=["POST"])
def refresh_investments_endpoint():
    """
    Refresh investments holdings for a linked investments item.
    Expects JSON with "user_id" and "item_id".
    """
    data = request.get_json()
    user_id = data.get("user_id")
    item_id = data.get("item_id")
    if not user_id or not item_id:
        return jsonify({"error": "Missing user_id or item_id"}), 400
    try:
        account = PlaidAccount.query.filter_by(
            item_id=item_id, product="investments"
        ).first()
        if not account:
            return jsonify({"error": "Investments account not found"}), 404
        investments_data = get_investments(account.access_token)
        # Process and save investments data as needed.
        # For example, you might call account_logic.process_investments(user_id, investments_data)
        return (
            jsonify(
                {
                    "status": "success",
                    "holdings_fetched": len(investments_data.get("holdings", [])),
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing investments: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
