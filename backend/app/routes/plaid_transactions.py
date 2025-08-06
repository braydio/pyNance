# file: app/routes/plaid_transactions.py
"""Endpoints for Plaid account linking and transaction sync."""

from datetime import datetime, timezone

from app.config import CLIENT_NAME, PLAID_CLIENT_ID, logger
from app.extensions import db
from app.helpers.plaid_helpers import (
    exchange_public_token,
    generate_link_token,
    get_accounts,
    get_institution_name,
    get_item,
    remove_item,
)
from app.models import Account, PlaidAccount
from app.sql import account_logic  # for upserting accounts and processing transactions
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

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
    frontend_user_id = data.get("user_id", "")
    user_id = frontend_user_id or CLIENT_NAME

    if not user_id:
        logger.error("No user_id available from frontend or env")
        return jsonify({"error": "user_id is required"}), 400

    logger.debug(
        f"user_id resolved from {'frontend' if frontend_user_id else 'env'}: {user_id}"
    )

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

        accounts = get_accounts(access_token, user_id)
        logger.debug(f"Retrieved {len(accounts)} accounts from Plaid")

        # --- PATCH: Persist PlaidAccount entries ---
        for acct in accounts:
            account_id = acct.get("account_id")
            if not account_id:
                continue

            exists = PlaidAccount.query.filter_by(account_id=account_id).first()
            if exists:
                logger.debug(f"PlaidAccount already exists for {account_id}")
                continue

            new_plaid_account = PlaidAccount(
                account_id=account_id,
                access_token=access_token,
                item_id=item_id,
                institution_id=institution_id,
                last_refreshed=datetime.now(timezone.utc),
            )
            db.session.add(new_plaid_account)

        for acct in accounts:
            acct["institution_name"] = institution_name
            logger.debug(
                f"Injected institution name into {len(accounts)} accounts: {institution_name}"
            )

        db.session.commit()

        logger.debug(f"[CHECK] Calling upsert_accounts() with user_id={user_id}")
        account_logic.upsert_accounts(
            user_id, accounts, provider="Plaid", access_token=access_token
        )
        logger.info(f"Upserted {len(accounts)} accounts for user {user_id}")

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


@plaid_transactions.route("/delete_account", methods=["DELETE"])
def delete_plaid_account():
    """Delete an account and revoke its Plaid item."""
    try:
        data = request.json
        account_id = data.get("account_id")
        logger.debug(f"Received request to delete account_id={account_id}")

        if not account_id:
            logger.warning("No account_id provided in request")
            return jsonify({"status": "error", "message": "Missing account_id"}), 400

        plaid_acct = PlaidAccount.query.filter_by(account_id=account_id).first()
        if plaid_acct and plaid_acct.access_token:
            try:
                remove_item(plaid_acct.access_token)
            except Exception as ex:
                logger.warning(f"Failed to remove Plaid item: {ex}")

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


@plaid_transactions.route("/refresh_accounts", methods=["POST"])
def refresh_accounts_endpoint():
    data = request.get_json()
    user_id = data.get("user_id")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    account_ids = data.get("account_ids") or []
    start_date = (
        datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    )
    end_date = (
        datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
    )
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        query = Account.query.options(joinedload(Account.plaid_account)).filter_by(
            user_id=user_id
        )
        if account_ids:
            query = query.filter(Account.account_id.in_(account_ids))
        accounts = query.all()
        refreshed = []
        for acct in accounts:
            if acct.plaid_account and acct.plaid_account.access_token:
                refreshed_flag, _ = account_logic.refresh_data_for_plaid_account(
                    access_token=acct.plaid_account.access_token,
                    account_id=acct.account_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                if refreshed_flag:
                    refreshed.append(
                        acct.name or acct.account_id
                    )  # ✅ return readable name
            else:
                logger.warning(
                    f"Missing access token for account {acct.account_id} (user {user_id})"
                )

        return jsonify({"status": "success", "updated_accounts": refreshed}), 200

    except Exception as e:
        logger.error(f"Error refreshing accounts: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
