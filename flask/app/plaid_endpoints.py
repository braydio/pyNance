import json
from datetime import datetime, timedelta

import requests
from app.db_models import SessionLocal
from app.helper_utils import process_transactions
from app.services.plaid_helpers import (
    ensure_file_exists,
    exchange_public_token,
    generate_link_token,
    get_item_info,
    load_json,
    save_initial_account_data,
    save_json_with_backup,
)
from config import FILES, PLAID_BASE_URL, PLAID_CLIENT_ID, PLAID_SECRET, logger

from flask import Blueprint, jsonify, request

# ------------------------------------------------------------------------------
# CORE PLAID BLUEPRINT (Link Token, Exchange Token, etc.)
# ------------------------------------------------------------------------------
plaid_core = Blueprint("plaid_core", __name__)


@plaid_core.route("/create_link_token", methods=["POST"])
def create_link_token_route():
    """
    Create a Plaid link token for the specified products (e.g. ["transactions"] or ["investments"]).
    """
    data = request.get_json() or {}
    products_list = data.get(
        "products", ["transactions"]
    )  # default to ["transactions"]

    link_token = generate_link_token(products_list)
    if link_token is None:
        return jsonify({"error": "Unable to create link token"}), 500

    return jsonify({"link_token": link_token}), 200


@plaid_core.route("/exchange_public_token", methods=["POST"])
def exchange_public_token_route():
    """
    Exchange a public token for an access token.
    Typically called after a user completes the Plaid Link flow.
    """
    data = request.get_json() or {}
    public_token = data.get("public_token")
    if not public_token:
        return jsonify({"error": "Missing public_token"}), 400

    access_token = exchange_public_token(public_token)
    if not access_token:
        return jsonify({"error": "Failed to exchange public token"}), 500

    # Optionally do more (e.g., store the token in DB)
    return jsonify({"access_token": access_token}), 200


# ------------------------------------------------------------------------------
# TRANSACTIONS BLUEPRINT
# ------------------------------------------------------------------------------
plaid_transactions = Blueprint("plaid_transactions", __name__)


@plaid_transactions.route("/plaid_link_transactions", methods=["POST"])
def link_transactions():
    """
    Save the public token, exchange for an access token, and
    retrieve & store item metadata for transactions.
    """
    try:
        if not request.is_json:
            logger.error("Invalid Content-Type; expected application/json")
            return jsonify({"error": "Content-Type must be application/json."}), 400

        data = request.get_json()
        logger.debug(f"Received data: {json.dumps(data, indent=2)}")

        public_token = data.get("public_token")
        if public_token:
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
                return jsonify({"error": "No access token was generated."}), 400
        else:
            logger.error("Missing public_token in request.")
            return jsonify({"error": "Missing public_token"}), 400
    except json.JSONDecodeError as jde:
        logger.error(f"JSON decode error: {jde}")
        return jsonify({"error": "Invalid JSON payload", "details": str(jde)}), 400
    except Exception as e:
        logger.error(f"Error processing public token: {e}", exc_info=True)
        return (
            jsonify(
                {
                    "error": "Server error while processing public token",
                    "details": str(e),
                }
            ),
            500,
        )


@plaid_transactions.route("/transactions_refresh", methods=["POST"])
def refresh_transactions():
    """
    Refresh transactions for a given item_id.
    """
    try:
        data = request.get_json() or {}
        item_id = data.get("item_id")
        if not item_id:
            logger.error("Missing item_id in request.")
            return jsonify({"error": "Missing item_id"}), 400

        # Load LinkedItems.json
        try:
            with open(FILES["LINKED_ITEMS"], "r") as f:
                linked_items = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error("LinkedItems.json missing or invalid.")
            return jsonify({"error": "LinkedItems.json not found or invalid."}), 500

        item = linked_items.get(item_id)
        if not item:
            logger.error(f"Item ID {item_id} not found in LinkedItems.json.")
            return jsonify({"error": f"Item ID {item_id} not found."}), 404

        # Gather date range
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Load linked accounts
        try:
            with open(FILES["LINKED_ACCOUNTS"], "r") as f:
                linked_accounts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error("LinkedAccounts.json missing or invalid.")
            return jsonify({"error": "LinkedAccounts.json not found or invalid."}), 500

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

        # Use requests.post, not request.post
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            transactions_data = response.json()
            logger.debug(f"Plaid API response: {transactions_data}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Plaid API error: {str(e)}")
            return jsonify({"error": f"Failed to fetch transactions: {str(e)}"}), 500

        # Save raw transactions
        with open(FILES["TRANSACTIONS_RAW"], "w") as f:
            json.dump(
                {"transactions": transactions_data.get("transactions", [])}, f, indent=4
            )
        raw_tx_count = len(transactions_data.get("transactions", []))
        logger.info(
            f"Saved {raw_tx_count} transactions to {FILES['TRANSACTIONS_RAW']}."
        )

        # Update linked_accounts with latest balances
        for account in transactions_data.get("accounts", []):
            acct_id = account["account_id"]
            if acct_id in linked_accounts:
                linked_accounts[acct_id]["balances"] = account["balances"]

        with open(FILES["LINKED_ACCOUNTS"], "w") as f:
            json.dump(linked_accounts, f, indent=4)

        # Update last refresh timestamp
        item.setdefault("status", {}).setdefault("transactions", {})[
            "last_successful_update"
        ] = datetime.now()
        linked_items[item_id] = item
        with open(FILES["LINKED_ITEMS"], "w") as f:
            json.dump(linked_items, f, indent=4)

        # Process/Enrich transactions as needed
        all_transactions = transactions_data.get("transactions", [])
        count_transactions = len(all_transactions)
        process_transactions(all_transactions, linked_accounts, linked_items)
        logger.info(
            f"Processed {count_transactions} transactions for item ID {item_id}."
        )

        # Optionally save to DB
        try:
            session = SessionLocal()  # from sql_utils.py
            # e.g. save_transactions_to_db(session, all_transactions)
            session.commit()
            logger.info("Transactions saved to the database.")
        except Exception as db_error:
            session.rollback()
            logger.error(f"Error saving transactions to DB: {db_error}", exc_info=True)
            return (
                jsonify(
                    {
                        "error": "Error saving transactions to database",
                        "details": str(db_error),
                    }
                ),
                500,
            )
        finally:
            session.close()

        logger.info(
            f"Refreshed account {item_id}. Fetched and processed {count_transactions} transactions."
        )
        return (
            jsonify({"status": "success", "transactions_fetched": count_transactions}),
            200,
        )

    except Exception as e:
        logger.error(f"Error in refresh_account: {e}", exc_info=True)
        return (
            jsonify(
                {"error": "Server error during transactions refresh", "details": str(e)}
            ),
            500,
        )


# ------------------------------------------------------------------------------
# INVESTMENTS BLUEPRINT
# ------------------------------------------------------------------------------
plaid_investments = Blueprint("plaid_investments", __name__)


@plaid_investments.route("/plaid_link_investments", methods=["GET"])
def get_investments_link_token():
    """
    Generate a link token specifically for 'investments'.
    The front-end can call this route when the investments
    view is toggled to initialize Plaid Link for investments.
    """
    try:
        link_token = generate_link_token(["investments"])
        if link_token:
            return jsonify({"status": "success", "link_token": link_token}), 200
        else:
            logger.error("Failed to create investments link token.")
            return jsonify({"error": "Failed to create link token"}), 500
    except Exception as e:
        logger.error(f"Error in get_investments_link_token: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


""" Has not yet been integrated
@plaid_investments.route("/save_investments_public_token", methods=["POST"])
def save_investments_public_token():
    
    # Save the public token for an investments item, exchange it for an access token,
    # retrieve the item info, and store the initial data.
    
    try:
        if not request.is_json:
            logger.error("Invalid Content-Type; expected application/json")
            return jsonify({"error": "Content-Type must be application/json."}), 400

        data = request.get_json() or {}
        public_token = data.get("public_token")
        if not public_token:
            logger.error("Missing public_token in request.")
            return jsonify({"error": "Missing public_token"}), 400

        # Save the token for auditing (optional)
        temp_file = os.path.join(
            DIRECTORIES["TEMP_DIR"], "investments_public_token.txt"
        )
        with open(temp_file, "w") as f:
            f.write(public_token)
        logger.info("Investments public token saved to file.")

        # Exchange the public token
        access_token = exchange_public_token(public_token)
        if not access_token:
            logger.error("Exchange failed; no access token generated.")
            return (
                jsonify({"error": "Exchange failed; no access token generated."}),
                400,
            )

        item_id, institution_name = get_item_info(access_token)
        if not item_id:
            logger.error("Failed to retrieve investments item metadata.")
            return (
                jsonify({"error": "Failed to retrieve investments item metadata"}),
                400,
            )

        # Save initial data
        save_initial_investments_data(access_token, item_id)
        logger.info(
            f"Linked investments item for {institution_name} (item ID: {item_id}) successfully."
        )

        # Save into linked_investments JSON
        ensure_file_exists(FILES["LINKED_INVESTMENT_ACCOUNTS"], default_content={})
        try:
            linked_items = load_json(FILES["LINKED_INVESTMENT_ACCOUNTS"])
        except Exception:
            linked_items = {}

        linked_items[item_id] = {
            "institution_name": institution_name,
            "item_id": item_id,
            "access_token": access_token,
            "linked_at": datetime.now().isoformat(),
            "status": {},
        }
        save_json_with_backup(FILES["LINKED_INVESTMENT_ACCOUNTS"], linked_items)

        # Save to DB (optional)
        try:
            db_session = SessionLocal()
            save_investment_account_to_db(
                db_session, item_id, institution_name, access_token, datetime.now()
            )
            db_session.commit()
            db_session.close()
            logger.info("Investments account saved to the database.")
        except Exception as db_e:
            logger.error(
                f"Error saving investments account to DB: {db_e}", exc_info=True
            )
            return jsonify({"error": f"DB error: {db_e}"}), 500

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

    except Exception as e:
        logger.error(f"Error processing investments public token: {e}", exc_info=True)
        return (
            jsonify(
                {
                    "error": "Server error while processing investments public token",
                    "details": str(e),
                }
            ),
            500,
        )
"""


@plaid_investments.route("/get_investments", methods=["GET"])
def get_investments():
    """
    Return all linked investments items as JSON.
    """
    try:
        linked_items = load_json(FILES["LINKED_INVESTMENT_ACCOUNTS"])
        return jsonify({"status": "success", "investments": linked_items}), 200
    except Exception as e:
        logger.error(f"Error loading linked investments: {e}")
        return jsonify({"error": "Could not load investments"}), 500


@plaid_investments.route("/investments_refresh", methods=["POST"])
def refresh_investments():
    """
    Refresh investments holdings data for a linked investments item.
    """
    data = request.get_json() or {}
    item_id = data.get("item_id")
    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

    try:
        linked_items = load_json(FILES["LINKED_INVESTMENT_ACCOUNTS"])
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
        # Use requests.post, not request.post
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        investments_data = response.json()
        logger.debug(f"Plaid Investments API response: {investments_data}")
    except Exception as e:
        logger.error(f"Error fetching investments data: {e}")
        return jsonify({"error": f"Failed to fetch investments data: {e}"}), 500

    # Save raw investments
    with open(FILES["INVESTMENTS_RAW"], "w") as f:
        json.dump(investments_data, f, indent=4)
    logger.info(f"Saved investments data to {FILES['INVESTMENTS_RAW']}.")

    # Update last refresh timestamp
    item.setdefault("status", {}).setdefault("holdings", {})[
        "last_successful_update"
    ] = datetime.now().isoformat()
    linked_items[item_id] = item
    save_json_with_backup(FILES["LINKED_INVESTMENT_ACCOUNTS"], linked_items)

    # Save holdings to a separate JSON (or DB)
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
