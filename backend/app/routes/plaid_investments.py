from app.config import logger
from app.helpers.plaid_helpers import (
    exchange_public_token,
    generate_link_token,
    get_accounts,
    get_investment_transactions,
    )
from app.models import PlaidAccount
from app.sql import investments_logic
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
        start_date = (request.get_json() or {}).get("start_date")
        end_date = (request.get_json() or {}).get("end_date")
        # Default to last 30 days if not provided
        if not start_date or not end_date:
            from datetime import date, timedelta

            end_date = date.today().isoformat()
            start_date = (date.today() - timedelta(days=30)).isoformat()
        account = PlaidAccount.query.filter_by(
            item_id=item_id, product="investments"
        ).first()
        if not account:
            return jsonify({"error": "Investments account not found"}), 404
        # Fetch holdings + securities and upsert
        summary = investments_logic.upsert_investments_from_plaid(
            user_id, account.access_token
        )
        # Fetch investment transactions and upsert
        txs = get_investment_transactions(account.access_token, start_date, end_date)
        tx_count = investments_logic.upsert_investment_transactions(txs)
        return (
            jsonify(
                {
                    "status": "success",
                    "upserts": {**summary, "investment_transactions": tx_count},
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing investments: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_investments.route("/refresh_all", methods=["POST"])
def refresh_all_investments():
    """Refresh holdings and transactions for all active Plaid investment items.

    Optional JSON body accepts start_date/end_date (YYYY-MM-DD); defaults last 30 days.
    """
    try:
        payload = request.get_json() or {}
        start_date = payload.get("start_date")
        end_date = payload.get("end_date")
        if not start_date or not end_date:
            from datetime import date, timedelta

            end_date = date.today().isoformat()
            start_date = (date.today() - timedelta(days=30)).isoformat()

        items = PlaidAccount.query.filter_by(
            product="investments", is_active=True
        ).all()
        total = {
            "securities": 0,
            "holdings": 0,
            "investment_transactions": 0,
            "items": len(items),
        }
        for pa in items:
            try:
                sums = investments_logic.upsert_investments_from_plaid(
                    pa.account.user_id if pa.account else None, pa.access_token
                )
                for k in ("securities", "holdings"):
                    total[k] += int(sums.get(k, 0))
                txs = get_investment_transactions(pa.access_token, start_date, end_date)
                total["investment_transactions"] += (
                    investments_logic.upsert_investment_transactions(txs)
                )
            except Exception as inner:
                logger.error(
                    f"Failed to refresh investments for item {pa.item_id}: {inner}"
                )
                continue

        return (
            jsonify(
                {
                    "status": "success",
                    "summary": total,
                    "range": {"start_date": start_date, "end_date": end_date},
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error in refresh_all_investments: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
