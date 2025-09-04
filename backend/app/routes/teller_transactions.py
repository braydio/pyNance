import json
from datetime import datetime, timezone

from app.config import FILES, TELLER_API_BASE_URL, logger
from app.extensions import db
from app.helpers.teller_helpers import load_tokens  # Use the shared helper
from app.models import Account, Transaction
from app.sql import account_logic
from flask import Blueprint, jsonify, request

teller_transactions = Blueprint("teller_transactions", __name__)

# In case later I want to split out Link Teller Account logic into its own routes
# teller_link = Blueprint("teller-link", __name__)


@teller_transactions.route("/save_access_token", methods=["POST"])
def save_teller_token():
    try:
        data = request.get_json()
        access_token = data.get("access_token")
        user_id = data.get("user_id", "default-user")

        if not access_token:
            logger.warning("Missing access token in request body.")
            return (
                jsonify({"status": "error", "message": "Access token is required."}),
                400,
            )

        logger.debug(f"Saving access token for user {user_id}")
        tokens = load_tokens()
        tokens.append({"user_id": user_id, "access_token": access_token})
        with open(FILES["TELLER_TOKENS"], "w") as f:
            json.dump(tokens, f, indent=4)

        logger.info("Access token saved successfully.")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Error saving Teller token: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_transactions.route("/exchange_public_token", methods=["POST"])
def teller_exchange_public_token():
    logger.error(
        "Teller does not have an exchange process. Save response as linked token."
    )
    return (
        jsonify(
            {
                "error": "You are looking for the /teller_transactions/save_access_token route. This incorrect route is being depreciated."
            }
        ),
        500,
    )


@teller_transactions.route("/refresh_accounts", methods=["POST"])
def teller_refresh_accounts():
    """
    Refresh Teller accounts and transactions using the stored tokens.
    """
    try:
        logger.debug("Refreshing Teller accounts from database.")
        accounts = Account.query.all()
        updated_accounts = []
        tokens = load_tokens()
        for account in accounts:
            access_token = None
            for token in tokens:
                if token.get("user_id") == account.user_id:
                    access_token = token.get("access_token")
                    break
            if not access_token:
                logger.warning(f"No access token found for user {account.user_id}")
                continue
            logger.debug(
                f"Refreshing Teller account {account.name} ({account.account_id}) with token: {access_token}"
            )
            updated = account_logic.refresh_data_for_teller_account(
                account,
                access_token,
                FILES["TELLER_DOT_CERT"],
                FILES["TELLER_DOT_KEY"],
                TELLER_API_BASE_URL,
            )
            if updated:
                updated_accounts.append(account.name)
                account.last_refreshed = datetime.now(timezone.utc)
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Teller account data refreshed",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing Teller accounts: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@teller_transactions.route("/get_transactions", methods=["GET"])
def teller_get_transactions():
    """
    Return paginated Teller transactions.
    """
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        category = request.args.get("category")

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else None
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        )

        transactions_list, total = account_logic.get_paginated_transactions(
            page,
            page_size,
            start_date=start_date,
            end_date=end_date,
            category=category,
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"transactions": transactions_list, "total": total},
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error fetching Teller transactions: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@teller_transactions.route("/list_teller_accounts", methods=["GET"])
def get_accounts():
    try:
        logger.debug("Fetching accounts from the database.")
        accounts = account_logic.get_accounts_from_db()
        logger.debug(f"Fetched {len(accounts)} accounts from DB.")
        return jsonify({"status": "success", "data": {"accounts": accounts}}), 200
    except Exception as e:
        logger.error(f"Error fetching accounts from DB: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_transactions.route("/refresh_balances", methods=["POST"])
def refresh_balances():
    """
    Refresh Teller account balances and update historical records.
    """
    try:
        accounts = account_logic.get_accounts_from_db()
        updated_accounts = []
        tokens = load_tokens()
        for acc in accounts:
            account = Account.query.filter_by(account_id=acc["account_id"]).first()
            if not account:
                logger.warning(f"Account {acc['account_id']} not found in DB.")
                continue
            access_token = None
            for token in tokens:
                if token.get("user_id") == acc["user_id"]:
                    access_token = token.get("access_token")
                    break
            if not access_token:
                logger.warning(f"No access token found for account {acc['account_id']}")
                continue
            updated = account_logic.refresh_data_for_teller_account(
                account,
                access_token,
                FILES["TELLER_DOT_CERT"],
                FILES["TELLER_DOT_KEY"],
                TELLER_API_BASE_URL,
            )
            if updated:
                updated_accounts.append({"account_name": acc["name"]})
        db.session.commit()
        logger.debug(f"Balances refreshed for accounts: {updated_accounts}")
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Balances refreshed",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error refreshing balances: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_transactions.route("/update", methods=["PUT"])
def update_transaction():
    """
    Update a transaction's editable details.
    """
    try:
        data = request.json
        transaction_id = data.get("transaction_id")
        if not transaction_id:
            return (
                jsonify({"status": "error", "message": "Missing transaction_id"}),
                400,
            )

        txn = Transaction.query.filter_by(transaction_id=transaction_id).first()
        if not txn:
            return jsonify({"status": "error", "message": "Transaction not found"}), 404

        changed_fields = {}
        if "amount" in data:
            txn.amount = float(data["amount"])
            changed_fields["amount"] = True
        if "date" in data:
            txn.date = data["date"]
            changed_fields["date"] = True
        if "description" in data:
            txn.description = data["description"]
            changed_fields["description"] = True
        if "category" in data:
            txn.category = data["category"]
            changed_fields["category"] = True
        if "merchant_name" in data:
            txn.merchant_name = data["merchant_name"]
            changed_fields["merchant_name"] = True
        if "merchant_type" in data:
            txn.merchant_type = data["merchant_type"]
            changed_fields["merchant_type"] = True

        txn.user_modified = True
        existing_fields = {}
        if txn.user_modified_fields:
            existing_fields = json.loads(txn.user_modified_fields)
        for field in changed_fields:
            existing_fields[field] = True
        txn.user_modified_fields = json.dumps(existing_fields)

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error updating transaction: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@teller_transactions.route("/delete_account", methods=["DELETE"])
def delete_teller_account():
    try:
        data = request.json
        account_id = data.get("account_id")
        if not account_id:
            return jsonify({"status": "error", "message": "Missing account_id"}), 400

        Account.query.filter_by(account_id=account_id).delete()
        db.session.commit()
        logger.info(
            f"Deleted Teller account {account_id} and related records via cascade."
        )
        return (
            jsonify(
                {"status": "success", "message": "Account and related records deleted"}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error deleting Teller account: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
