# app/routes/plaid.py
import json
from datetime import datetime, timedelta

from app.helper_utils import process_transactions
from app.services.plaid_helpers import generate_link_token, process_access_token
from config import FILES, PLAID_BASE_URL, PLAID_CLIENT_ID, PLAID_SECRET, logger

from flask import Blueprint, jsonify, request

plaid_api = Blueprint("plaid_api", __name__, url_prefix="/api/plaid")


@plaid_api.route("/create_link_token", methods=["POST"])
def create_link_token_route():
    data = request.get_json() or {}
    products = data.get("products", ["transactions"])
    link_token = generate_link_token(products)
    if not link_token:
        return jsonify({"error": "Unable to create link token"}), 500
    return jsonify({"link_token": link_token}), 200


@plaid_api.route("/exchange_public_token", methods=["POST"])
def exchange_public_token_route():
    data = request.get_json() or {}
    public_token = data.get("public_token")
    provider = data.get("provider", "plaid")
    if not public_token:
        return jsonify({"error": "Missing public token"}), 400
    result, status = process_access_token(public_token, provider)
    return jsonify(result), status


@plaid_api.route("/transactions_refresh", methods=["POST"])
def refresh_transactions():
    data = request.get_json() or {}
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

    try:
        with open(FILES["LINKED_ITEMS"], "r") as f:
            linked_items = json.load(f)
    except Exception:
        logger.error("LinkedItems file error.")
        return jsonify({"error": "LinkedItems file not found or invalid."}), 500

    item = linked_items.get(item_id)
    if not item:
        return jsonify({"error": f"Item ID {item_id} not found."}), 404

    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(FILES["LINKED_ACCOUNTS"], "r") as f:
            linked_accounts = json.load(f)
    except Exception:
        logger.error("LinkedAccounts file error.")
        return jsonify({"error": "LinkedAccounts file not found or invalid."}), 500

    access_token = next(
        (
            acc.get("access_token")
            for acc in linked_accounts.values()
            if acc.get("item_id") == item_id
        ),
        None,
    )
    if not access_token:
        return jsonify({"error": f"No access token for item ID {item_id}."}), 400

    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
        "start_date": start_date,
        "end_date": end_date,
    }
    url = f"{PLAID_BASE_URL}/transactions/get"
    try:
        response = request.post(url, json=payload, timeout=10)
        response.raise_for_status()
        transactions_data = response.json()
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({"error": f"Failed to fetch transactions: {e}"}), 500

    with open(FILES["TRANSACTIONS_RAW"], "w") as f:
        json.dump(
            {"transactions": transactions_data.get("transactions", [])}, f, indent=4
        )

    # Update last refresh timestamp
    item.setdefault("status", {}).setdefault("transactions", {})[
        "last_successful_update"
    ] = datetime.now().isoformat()
    linked_items[item_id] = item
    with open(FILES["LINKED_ITEMS"], "w") as f:
        json.dump(linked_items, f, indent=4)

    # Process transactions (this function might save to DB too)
    process_transactions(
        transactions_data.get("transactions", []), linked_accounts, linked_items
    )

    return (
        jsonify(
            {
                "status": "success",
                "transactions_fetched": len(transactions_data.get("transactions", [])),
            }
        ),
        200,
    )


# Similar endpoints for investments could be defined under the same blueprint or in a separate blueprint.
