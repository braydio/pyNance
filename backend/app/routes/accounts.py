from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import RecurringTransaction

# Blueprint for generic accounts routes
accounts = Blueprint("accounts", __name__)

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
