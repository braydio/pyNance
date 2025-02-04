import json
import os
from datetime import datetime, timedelta

import requests
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
    load_json,
    save_initial_investments_data,
    save_json_with_backup,
)
from sql_utils import Session

# Create the blueprint for standard (transactions) endpoints.
plaid_transactions = Blueprint("plaid", __name__)


@plaid_transactions.route("/delete_account", methods=["POST"])
def delete_account():
    """
    Delete a linked account and, if no other accounts remain for the same institution,
    delete the institution from the linked items.
    Expects a JSON payload with:
      - account_id: The ID of the account to delete.
    """
    data = request.get_json()
    account_id = data.get("account_id")
    if not account_id:
        logger.error("Missing account_id in delete request.")
        return jsonify({"error": "Missing account_id"}), 400

    # Load the linked accounts JSON.
    try:
        linked_accounts = load_json(FILES["LINKED_ACCOUNTS"])
    except Exception:
        logger.error("LinkedAccounts.json missing or invalid.")
        return jsonify({"error": "LinkedAccounts.json not found or invalid."}), 500

    if account_id not in linked_accounts:
        logger.error(f"Account {account_id} not found in linked accounts.")
        return jsonify({"error": f"Account {account_id} not found."}), 404

    # Save details of the account to be deleted before removal.
    deleted_account = linked_accounts[account_id]
    deleted_item_id = deleted_account.get("item_id")
    deleted_institution_name = deleted_account.get("institution_name")

    # Delete the account from the linked_accounts.
    del linked_accounts[account_id]
    try:
        save_json_with_backup(FILES["LINKED_ACCOUNTS"], linked_accounts)
        logger.info(f"Deleted account {account_id} from linked accounts.")
    except Exception as e:
        logger.error(f"Error saving linked accounts after deletion: {e}")
        return jsonify({"error": f"Failed to delete account {account_id}: {e}"}), 500

    # Check if any other accounts remain for the same institution (by item_id).
    institution_exists = any(
        acc.get("item_id") == deleted_item_id for acc in linked_accounts.values()
    )

    # If no accounts remain for that institution, delete the institution from linked items.
    if not institution_exists:
        try:
            linked_items = load_json(FILES["LINKED_ITEMS"])
        except Exception:
            logger.error("LinkedItems.json missing or invalid.")
            return jsonify({"error": "LinkedItems.json not found or invalid."}), 500

        if deleted_item_id in linked_items:
            del linked_items[deleted_item_id]
            try:
                save_json_with_backup(FILES["LINKED_ITEMS"], linked_items)
                logger.info(
                    f"Deleted institution '{deleted_institution_name}' (item_id: {deleted_item_id}) from linked items."
                )
            except Exception as e:
                logger.error(f"Error saving linked items after deletion: {e}")
                return (
                    jsonify(
                        {
                            "error": f"Failed to delete institution for account {account_id}: {e}"
                        }
                    ),
                    500,
                )

    return (
        jsonify(
            {
                "status": "success",
                "message": f"Account {account_id} deleted; institution removed if no other accounts remain.",
            }
        ),
        200,
    )


@plaid_transactions.route("/transactions_refresh", methods=["POST"])
def refresh_account():
    try:
        # --- Validate Input ---
        data = request.get_json()
        item_id = data.get("item_id")
        if not item_id:
            logger.error("Missing item_id in request.")
            return jsonify({"error": "Missing item_id"}), 400

        # --- Load Linked Items ---
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

        # --- Set Date Range ---
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        # --- Load Linked Accounts ---
        try:
            with open(FILES["LINKED_ACCOUNTS"], "r") as f:
                linked_accounts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error("LinkedAccounts.json missing or invalid.")
            return jsonify({"error": "LinkedAccounts.json not found or invalid."}), 500

        # --- Retrieve Access Token ---
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

        # --- Fetch Transactions from Plaid ---
        payload = {
            "client_id": PLAID_CLIENT_ID,
            "secret": PLAID_SECRET,
            "access_token": access_token,
            "start_date": start_date,
            "end_date": end_date,
        }
        url = f"{PLAID_BASE_URL}/transactions/get"
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            transactions_data = response.json()
            logger.debug(f"Plaid API response: {transactions_data}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Plaid API error: {str(e)}")
            return jsonify({"error": f"Failed to fetch transactions: {str(e)}"}), 500

        # --- Save Raw Transactions for Auditing ---
        with open(FILES["TRANSACTIONS_RAW"], "w") as f:
            json.dump(
                {"transactions": transactions_data.get("transactions", [])}, f, indent=4
            )
        raw_tx_count = len(transactions_data.get("transactions", []))
        logger.info(
            f"Saved {raw_tx_count} transactions to {FILES['TRANSACTIONS_RAW']}."
        )

        # --- Update Linked Accounts with Latest Balances ---
        for account in transactions_data.get("accounts", []):
            account_id = account["account_id"]
            if account_id in linked_accounts:
                linked_accounts[account_id]["balances"] = account["balances"]

        with open(FILES["LINKED_ACCOUNTS"], "w") as f:
            json.dump(linked_accounts, f, indent=4)

        # --- Update Last Refresh Timestamp ---
        item.setdefault("status", {}).setdefault("transactions", {})[
            "last_successful_update"
        ] = datetime.now().isoformat()
        linked_items[item_id] = item
        with open(FILES["LINKED_ITEMS"], "w") as f:
            json.dump(linked_items, f, indent=4)

        # --- Process (Enrich & Deduplicate) Transactions ---
        all_transactions = transactions_data.get("transactions", [])
        count_transactions = len(all_transactions)
        process_transactions(all_transactions, linked_accounts, linked_items)
        logger.info(
            f"Processed {count_transactions} transactions for item ID {item_id}."
        )

        # --- Save Transactions to the SQL Database ---
        try:
            session = Session()  # Create a new database session
            # Pass the raw transactions (or you might pass the enriched ones depending on your logic)
            # save_transactions_to_db(session, all_transactions, linked_accounts)
            session.commit()
            logger.info("Transactions saved to the database.")
        except Exception as e:
            session.rollback()
            logger.error(
                f"Error saving transactions to the database: {e}", exc_info=True
            )
            return (
                jsonify(
                    {
                        "error": "Error saving transactions to database",
                        "details": str(e),
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
