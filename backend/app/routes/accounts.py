from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import RecurringTransaction, Account
from app.sql.forecast_logic import update_account_history
from app.utils.finance_utils import normalize_account_balance
from app.config import logger

# Blueprint for generic accounts routes
accounts = Blueprint("accounts", __name__)


@accounts.route("/refresh_accounts", methods=["POST"])
def refresh_all_accounts():
    """
    Unified endpoint to refresh account data for all providers (Plaid + Teller).
    Iterates through all accounts and refreshes data based on link_type.
    """
    try:
        logger.debug("Starting refresh of all linked accounts.")
        accounts = Account.query.all()
        updated_accounts = []

        # Load Teller tokens once
        teller_tokens = load_tokens()

        for account in accounts:
            if account.link_type == "Plaid":
                access_token = account.access_token
                if not access_token:
                    logger.warning(f"No Plaid token for {account.account_id}")
                    continue

                logger.debug(f"Refreshing Plaid account {account.account_id}")
                updated = account_logic.refresh_data_for_plaid_account(
                    access_token, PLAID_BASE_URL
                )
                if updated:
                    account.last_refreshed = datetime.utcnow()
                    updated_accounts.append(account.name)

            elif account.link_type == "Teller":
                access_token = None
                for token in teller_tokens:
                    if token.get("user_id") == account.user_id:
                        access_token = token.get("access_token")
                        break
                if not access_token:
                    logger.warning(f"No Teller token for {account.account_id}")
                    continue

                logger.debug(f"Refreshing Teller account {account.account_id}")
                updated = account_logic.refresh_data_for_teller_account(
                    account,
                    access_token,
                    FILES["TELLER_DOT_CERT"],
                    FILES["TELLER_DOT_KEY"],
                    TELLER_API_BASE_URL,
                )
                if updated:
                    account.last_refreshed = datetime.utcnow()
                    updated_accounts.append(account.name)

            else:
                logger.info(
                    f"Skipping account {account.account_id} with unknown link_type {account.link_type}"
                )

        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "All linked accounts refreshed.",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error in unified refresh_accounts: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        include_hidden = (
            request.args.get("include_hidden", "false").lower() == "true"
        )
        query = Account.query
        if not include_hidden:
            query = query.filter(Account.is_hidden.is_(False))
        accounts = query.all()
        data = []
        for a in accounts:
            try:
                last_refreshed = None
                if a.plaid_account and a.plaid_account.last_refreshed:
                    last_refreshed = a.plaid_account.last_refreshed
                elif a.teller_account and a.teller_account.last_refreshed:
                    last_refreshed = a.teller_account.last_refreshed
                normalized_balance = normalize_account_balance(a.balance, a.type)
                logger.info(
                    f"Normalized original balance of {a.balance} to {normalized_balance} because account type {a.type}"
                )

                data.append(
                    {
                        "id": a.id,
                        "name": a.name,
                        "institution_name": a.institution_name,
                        "type": a.type,
                        "balance": normalized_balance,
                        "subtype": a.subtype,
                        "link_type": a.link_type,
                        "last_refreshed": last_refreshed,
                        "is_hidden": a.is_hidden,
                    }
                )
            except Exception as item_err:
                logger.warning(
                    f"Error serializing account ID {a.id}: {item_err}", exc_info=True
                )
        return jsonify({"status": "success", "accounts": data}), 200
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/<account_id>/recurring", methods=["GET"])
def get_recurring(account_id):
    """
    Endpoint to get merged recurring transactions for a given account.
    Retrieves all recurring transactions for the specified account from the database.
    """
    try:
        recurring_txs = RecurringTransaction.query.filter_by(
            account_id=account_id
        ).all()
        data = []
        for tx in recurring_txs:
            data.append(
                {
                    "id": tx.id,
                    "description": tx.description,
                    "amount": tx.amount,
                    "frequency": tx.frequency,
                    "next_due_date": (
                        tx.next_due_date.isoformat() if tx.next_due_date else None
                    ),
                    "notes": tx.notes,
                    "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
                }
            )
        return jsonify({"status": "success", "reminders": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/<account_id>/recurringTx", methods=["PUT"])
def update_recurring_tx(account_id):
    """
    Endpoint to update a recurring transaction for a given account.
    Expects JSON payload with at least an "amount" field.
    If no recurring transaction exists for the account, a new one is created.
    """
    data = request.get_json()
    if not data or "amount" not in data:
        return (
            jsonify({"status": "error", "message": "Missing 'amount' in request body"}),
            400,
        )

    amount = data["amount"]
    try:
        recurring = RecurringTransaction.query.filter_by(account_id=account_id).first()
        if recurring:
            recurring.amount = amount
            db.session.commit()
            return (
                jsonify(
                    {"status": "success", "message": "Recurring transaction updated"}
                ),
                200,
            )
        else:
            # Create a new recurring transaction with a default description and frequency if not provided.
            description = data.get("description", "Recurring Transaction")
            frequency = data.get("frequency", "monthly")
            new_tx = RecurringTransaction(
                account_id=account_id,
                description=description,
                amount=amount,
                frequency=frequency,
            )
            db.session.add(new_tx)
            db.session.commit()
            return (
                jsonify(
                    {"status": "success", "message": "Recurring transaction created"}
                ),
                201,
            )
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/<account_id>/hidden", methods=["PUT"])
def set_account_hidden(account_id):
    """Toggle an account's hidden status."""
    data = request.get_json() or {}
    hidden = bool(data.get("hidden", True))
    try:
        account = Account.query.filter_by(account_id=account_id).first()
        if not account:
            return (
                jsonify({"status": "error", "message": "Account not found"}),
                404,
            )
        account.is_hidden = hidden
        db.session.commit()
        update_account_history(
            account_id=account.account_id,
            user_id=account.user_id,
            balance=account.balance,
            is_hidden=account.is_hidden,
        )
        return jsonify({"status": "success", "hidden": account.is_hidden}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/match", methods=["POST"])
def match_account_by_fields():
    try:
        data = request.get_json()
        query = Account.query

        filters = []
        if data.get("account_id"):
            filters.append(Account.account_id == data["account_id"])
        if data.get("name"):
            filters.append(Account.name.ilike(f"%{data['name']}%"))
        if data.get("institution_name"):
            filters.append(
                Account.institution_name.ilike(f"%{data['institution_name']}%")
            )
        if data.get("type"):
            filters.append(Account.type == data["type"])
        if data.get("subtype"):
            filters.append(Account.subtype == data["subtype"])

        if filters:
            from sqlalchemy import or_

            matches = query.filter(or_(*filters)).all()
        else:
            matches = []

        return jsonify(
            [
                {
                    "account_id": acc.account_id,
                    "name": acc.name,
                    "institution_name": acc.institution_name,
                    "type": acc.type,
                    "subtype": acc.subtype,
                }
                for acc in matches
            ]
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
