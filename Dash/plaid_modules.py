import json
import os
from datetime import datetime, timedelta

from config import (
    DIRECTORIES,
    FILES,
    PLAID_BASE_URL,
    PLAID_CLIENT_ID,
    PLAID_SECRET,
    logger,
)
from flask import Blueprint, jsonify, request
from helper_utils import process_transactions
from plaid_helpers import (
    ensure_file_exists,
    exchange_public_token,
    get_investments_item_info,
    get_item_info,
    load_json,
    save_initial_account_data,
    save_initial_investments_data,
    save_json_with_backup,
)

# Main Plaid Routes for linking accounts, refreshing accounts
# Support for Transactions, Investments. To Do: Balances, Liabilities
# Create the blueprint for standard (transactions) endpoints.
plaid = Blueprint("plaid", __name__)


@plaid.route("/plaid_link_transactions", methods=["POST"])
def link_transactions():
    """
    Save the public token, exchange for an access token, and
    retrieve & store item metadata.
    """
    try:
        if not request.is_json:
            logger.error("Invalid Content-Type; expected application/json")
            return jsonify({"error": "Content-Type must be application/json."}), 400

        data = request.get_json()
        logger.debug(f"Received data: {json.dumps(data, indent=2)}")
        public_token = data.get("public_token")
        if public_token:
            # Save public token for debugging/auditing.
            # with open(os.path.join(DIRECTORIES["TEMP_DIR"], "public_token.txt"), "w") as f:
            #     f.write(public_token)
            # logger.info("Public token saved to file.")

            access_token = exchange_public_token(public_token)
            if access_token:
                item_id, institution_name = get_item_info(access_token)
                if item_id:
                    save_initial_account_data(access_token, item_id)
                    logger.info(
                        f"Linked to {institution_name} (item ID: {item_id}) successfully."
                    )
                    return (
                        jsonify(
                            {
                                "message": f"Linked to {institution_name} successfully",
                                "access_token": access_token,
                            }
                        ),
                        200,
                    )
                else:
                    logger.error("Failed to retrieve item metadata.")
                    return jsonify({"error": "Failed to retrieve item metadata"}), 400
            else:
                logger.error("Exchange failed; no access token generated.")
                return jsonify({"error": "No public token provided"}), 400
        else:
            logger.error("Missing public_token in request.")
            return jsonify({"error": "Missing public_token"}), 400
    except json.JSONDecodeError as jde:
        logger.error(f"JSON decode error: {jde}")
        return jsonify({"error": "Invalid JSON payload", "details": str(jde)}), 400
    except Exception as e:
        logger.error(f"Error processing public token: {e}")
        return (
            jsonify(
                {
                    "error": "Server error while processing public token",
                    "details": str(e),
                }
            ),
            500,
        )


@plaid.route("/transactions_refresh", methods=["POST"])
def refresh_account():
    """
    Refresh transactions data for a linked item.
    """
    data = request.get_json()
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

    try:
        linked_items = load_json(FILES["LINKED_ITEMS"])
    except Exception:
        logger.error("LinkedItems.json missing or invalid.")
        return jsonify({"error": "LinkedItems.json not found or invalid."}), 500

    item = linked_items.get(item_id)
    if not item:
        logger.error(f"Item ID {item_id} not found.")
        return jsonify({"error": f"Item ID {item_id} not found."}), 404

    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        linked_accounts = load_json(FILES["LINKED_ACCOUNTS"])
    except Exception:
        logger.error("LinkedAccounts.json missing or invalid.")
        return jsonify({"error": "LinkedAccounts.json not found or invalid."}), 500

    # Look up the access token by matching item_id in linked_accounts.
    access_token = next(
        (
            acc.get("access_token")
            for acc in linked_accounts.values()
            if acc.get("item_id") == item_id
        ),
        None,
    )
    if not access_token:
        logger.error(f"No access token for item ID {item_id}.")
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
        logger.debug(f"Plaid API response: {transactions_data}")
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({"error": f"Failed to fetch transactions: {e}"}), 500

    # Save raw transactions data so can review.
    with open(FILES["TRANSACTIONS_RAW"], "w") as f:
        json.dump(
            {"transactions": transactions_data.get("transactions", [])}, f, indent=4
        )
    logger.info(f"Saved {len(transactions_data.get('transactions', []))} transactions.")
    logger.debug("Refreshed Account in Plaid Route, proceed to processing.")

    # Proceed to processing.
    process_transactions(transactions_data, linked_accounts, linked_items)
    logger.info(
        f"Refreshed account {item_id}. Fetched {len(transactions_data.get('transactions', []))} transactions."
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
    # for account in transactions_data.get("accounts", []):
    #     account_id = account["account_id"]
    #     if account_id in linked_accounts:
    #         linked_accounts[account_id]["balances"] = account["balances"]

    # save_json_with_backup(FILES["LINKED_ACCOUNTS"], linked_accounts)

    # Update the last refresh timestamp in the linked item.
    # item.setdefault("status", {}).setdefault("transactions", {})["last_successful_update"] = datetime.now().isoformat()
    # linked_items[item_id] = item
    # save_json_with_backup(FILES["LINKED_ITEMS"], linked_items)

    # (Optional) Save transactions to a database.
    # save_transactions_to_db(transactions_data.get("transactions", []), linked_accounts)
    # save_recent_refresh_to_db(...)


# -------------------------
# Investments Endpoints
# -------------------------
plaid_investments = Blueprint("plaid_investments", __name__)


@plaid_investments.route("/save_investments_public_token", methods=["POST"])
def save_investments_public_token():
    """
    Save the public token for an investments item, exchange it for an access token,
    and store initial investments data.
    """
    try:
        if not request.is_json:
            logger.error("Invalid Content-Type; expected application/json")
            return jsonify({"error": "Content-Type must be application/json."}), 400

        data = request.get_json()
        logger.debug(f"Investments POST data: {json.dumps(data, indent=2)}")
        public_token = data.get("public_token")
        if public_token:
            # Save the public token for reference.
            with open(
                os.path.join(DIRECTORIES["TEMP_DIR"], "investments_public_token.txt"),
                "w",
            ) as f:
                f.write(public_token)
            logger.info("Investments public token saved to file.")

            access_token = exchange_public_token(public_token)
            if access_token:
                item_id, institution_name = get_investments_item_info(access_token)
                if item_id:
                    save_initial_investments_data(access_token, item_id)
                    logger.info(
                        f"Linked investments item for {institution_name} (item ID: {item_id}) successfully."
                    )

                    ensure_file_exists(FILES["LINKED_INVESTMENTS"], default_content={})
                    try:
                        linked_items = load_json(FILES["LINKED_INVESTMENTS"])
                    except Exception:
                        linked_items = {}

                    linked_items[item_id] = {
                        "institution_name": institution_name,
                        "item_id": item_id,
                        "access_token": access_token,
                        "linked_at": datetime.now().isoformat(),
                        "status": {},
                    }
                    save_json_with_backup(FILES["LINKED_INVESTMENTS"], linked_items)

                    return (
                        jsonify(
                            {
                                "message": f"Investments item linked to {institution_name} successfully.",
                                "access_token": access_token,
                                "item_id": item_id,
                            }
                        ),
                        200,
                    )
                else:
                    logger.error("Failed to retrieve investments item metadata.")
                    return (
                        jsonify(
                            {"error": "Failed to retrieve investments item metadata"}
                        ),
                        400,
                    )
            else:
                logger.error("No public token provided.")
                return jsonify({"error": "No public token provided"}), 400
        else:
            logger.error("Missing public_token in request.")
            return jsonify({"error": "Missing public_token"}), 400
    except Exception as e:
        logger.error(f"Error processing investments public token: {e}")
        return (
            jsonify(
                {
                    "error": "Server error while processing investments public token",
                    "details": str(e),
                }
            ),
            500,
        )


@plaid_investments.route("/investments_refresh", methods=["POST"])
def refresh_investments():
    """
    Refresh investments holdings data for a linked investments item.
    """
    data = request.get_json()
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

    try:
        linked_items = load_json(FILES["LINKED_INVESTMENTS"])
    except Exception:
        logger.error("LinkedInvestments.json missing or invalid.")
        return jsonify({"error": "LinkedInvestments.json not found or invalid."}), 500

    item = linked_items.get(item_id)
    if not item:
        logger.error(f"Investments item ID {item_id} not found.")
        return jsonify({"error": f"Item ID {item_id} not found."}), 404

    access_token = item.get("access_token")
    if not access_token:
        logger.error(f"No access token for investments item ID {item_id}.")
        return jsonify({"error": f"No access token for item ID {item_id}."}), 400

    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    url = f"{PLAID_BASE_URL}/investments/holdings/get"
    try:
        response = request.post(url, json=payload, timeout=10)
        response.raise_for_status()
        investments_data = response.json()
        logger.debug(f"Plaid Investments API response: {investments_data}")
    except Exception as e:
        logger.error(f"Error fetching investments data: {e}")
        return jsonify({"error": f"Failed to fetch investments data: {e}"}), 500

    # Save raw investments data.
    with open(FILES["INVESTMENTS_RAW"], "w") as f:
        json.dump(investments_data, f, indent=4)
    logger.info(f"Saved investments data to {FILES['INVESTMENTS_RAW']}.")

    # Update last refresh timestamp.
    item.setdefault("status", {}).setdefault("holdings", {})[
        "last_successful_update"
    ] = datetime.now().isoformat()
    linked_items[item_id] = item
    save_json_with_backup(FILES["LINKED_INVESTMENTS"], linked_items)

    # Save investments holdings details.
    ensure_file_exists(FILES["LINKED_INVESTMENT_ACCOUNTS"], default_content={})
    try:
        investment_accounts = load_json(FILES["LINKED_INVESTMENT_ACCOUNTS"])
    except Exception:
        investment_accounts = {}

    for holding in investments_data.get("holdings", []):
        account_id = holding.get("account_id")
        investment_accounts[account_id] = holding

    save_json_with_backup(FILES["LINKED_INVESTMENT_ACCOUNTS"], investment_accounts)
    total_holdings = len(investments_data.get("holdings", []))
    logger.info(
        f"Refreshed investments item {item_id}. Fetched {total_holdings} holdings."
    )
    return jsonify({"status": "success", "holdings_fetched": total_holdings}), 200
