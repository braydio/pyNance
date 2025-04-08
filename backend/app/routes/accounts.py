from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import RecurringTransaction
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
    """
    Generic endpoint to fetch accounts.
    Routes the request to the appropriate provider-specific endpoint based on the 'provider'
    query parameter. Defaults to 'teller' if not provided.
    """
    provider = request.args.get("provider", "teller").lower()
    if provider == "plaid":
        # Import and call the Plaid get_accounts endpoint
        from app.routes.plaid import get_accounts as plaid_get_accounts
        return plaid_get_accounts()
    elif provider == "teller":
        # Import and call the Teller get_accounts endpoint
        from app.routes.teller_transactions import get_accounts as teller_get_accounts
        return teller_get_accounts()
    else:
        return jsonify({"status": "error", "message": "Invalid provider specified"}), 400

@accounts.route("/<account_id>/recurring", methods=["GET"])
def get_recurring(account_id):
    """
    Endpoint to get merged recurring transactions for a given account.
    Retrieves all recurring transactions for the specified account from the database.
    """
    try:
        recurring_txs = RecurringTransaction.query.filter_by(account_id=account_id).all()
        data = []
        for tx in recurring_txs:
            data.append({
                "id": tx.id,
                "description": tx.description,
                "amount": tx.amount,
                "frequency": tx.frequency,
                "next_due_date": tx.next_due_date.isoformat() if tx.next_due_date else None,
                "notes": tx.notes,
                "updated_at": tx.updated_at.isoformat() if tx.updated_at else None
            })
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
        return jsonify({"status": "error", "message": "Missing 'amount' in request body"}), 400

    amount = data["amount"]
    try:
        recurring = RecurringTransaction.query.filter_by(account_id=account_id).first()
        if recurring:
            recurring.amount = amount
            db.session.commit()
            return jsonify({"status": "success", "message": "Recurring transaction updated"}), 200
        else:
            # Create a new recurring transaction with a default description and frequency if not provided.
            description = data.get("description", "Recurring Transaction")
            frequency = data.get("frequency", "monthly")
            new_tx = RecurringTransaction(
                account_id=account_id,
                description=description,
                amount=amount,
                frequency=frequency
            )
            db.session.add(new_tx)
            db.session.commit()
            return jsonify({"status": "success", "message": "Recurring transaction created"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
