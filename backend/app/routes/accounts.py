"""Account management and refresh routes."""

from datetime import datetime

from app.config import logger
from app.extensions import db
from app.models import Account, RecurringTransaction
from app.sql.forecast_logic import update_account_history
from app.utils.finance_utils import normalize_account_balance
from flask import Blueprint, jsonify, request

# Blueprint for generic accounts routes
accounts = Blueprint("accounts", __name__)


@accounts.route("/refresh_accounts", methods=["POST"])
def refresh_all_accounts():
    """Refresh all linked accounts.

    Iterates through every account and refreshes data for the appropriate
    provider. Returns a list of updated account names and a mapping of
    ``institution_name`` to refresh count under ``refreshed_counts``.
    """
    try:
        from app.config import FILES, TELLER_API_BASE_URL
        from app.sql import account_logic

        data = request.get_json() or {}
        account_ids = data.get("account_ids") or []
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        logger.debug("Starting refresh of all linked accounts.")

        query = Account.query
        if account_ids:
            query = query.filter(Account.account_id.in_(account_ids))
        accounts = query.all()
        updated_accounts = []
        refreshed_counts: dict[str, int] = {}

        # Load Teller tokens once
        from app.helpers.teller_helpers import load_tokens

        teller_tokens = load_tokens()

        for account in accounts:
            if account.link_type == "Plaid":
                access_token = None
                if account.plaid_account:
                    access_token = account.plaid_account.access_token
                if not access_token:
                    logger.warning(f"No Plaid token for {account.account_id}")
                    continue

                logger.debug(f"Refreshing Plaid account {account.account_id}")
                updated = account_logic.refresh_data_for_plaid_account(
                    access_token,
                    account.account_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                if updated and account.plaid_account:
                    account.plaid_account.last_refreshed = datetime.utcnow()
                    updated_accounts.append(account.name)
                    inst = account.institution_name or "Unknown"
                    refreshed_counts[inst] = refreshed_counts.get(inst, 0) + 1

            elif account.link_type == "Teller":
                access_token = None
                for token in teller_tokens:
                    if token.get("user_id") == account.user_id:
                        access_token = token.get("access_token")
                        break
                if not access_token and account.teller_account:
                    access_token = account.teller_account.access_token
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
                    start_date=start_date,
                    end_date=end_date,
                )
                if updated and account.teller_account:
                    account.teller_account.last_refreshed = datetime.utcnow()
                    updated_accounts.append(account.name)
                    inst = account.institution_name or "Unknown"
                    refreshed_counts[inst] = refreshed_counts.get(inst, 0) + 1

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
                    "refreshed_counts": refreshed_counts,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error in unified refresh_accounts: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/<account_id>/refresh", methods=["POST"])
def refresh_single_account(account_id):
    """Refresh a single account with an optional date range."""
    from app.config import FILES, TELLER_API_BASE_URL
    from app.sql import account_logic

    data = request.get_json() or {}
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    account = Account.query.filter_by(account_id=account_id).first()
    if not account:
        return jsonify({"status": "error", "message": "Account not found"}), 404

    updated = False

    if account.link_type == "Plaid":
        token = getattr(account.plaid_account, "access_token", None)
        if not token:
            return (
                jsonify({"status": "error", "message": "Missing Plaid token"}),
                400,
            )
        updated = account_logic.refresh_data_for_plaid_account(
            token,
            account_id,
            start_date=start_date,
            end_date=end_date,
        )
        if updated and account.plaid_account:
            account.plaid_account.last_refreshed = datetime.utcnow()

    elif account.link_type == "Teller":
        access_token = None
        from app.helpers.teller_helpers import load_tokens

        tokens = load_tokens()
        for t in tokens:
            if t.get("user_id") == account.user_id:
                access_token = t.get("access_token")
                break
        if not access_token and account.teller_account:
            access_token = account.teller_account.access_token
        if not access_token:
            return (
                jsonify({"status": "error", "message": "Missing Teller token"}),
                400,
            )
        updated = account_logic.refresh_data_for_teller_account(
            account,
            access_token,
            FILES["TELLER_DOT_CERT"],
            FILES["TELLER_DOT_KEY"],
            TELLER_API_BASE_URL,
            start_date=start_date,
            end_date=end_date,
        )
        if updated and account.teller_account:
            account.teller_account.last_refreshed = datetime.utcnow()
    else:
        return (
            jsonify({"status": "error", "message": "Unsupported link type"}),
            400,
        )

    if updated:
        db.session.commit()
    else:
        db.session.rollback()

    return jsonify({"status": "success", "updated": updated}), 200


@accounts.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        include_hidden = request.args.get("include_hidden", "false").lower() == "true"
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
                        "account_id": a.account_id,
                        "name": a.name,
                        "institution_name": a.institution_name,
                        "type": a.type,
                        "balance": normalized_balance,
                        "adjusted_balance": normalized_balance,
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
