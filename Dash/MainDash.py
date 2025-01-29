import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import requests

# All paths & files defined in config
from config import (
    DIRECTORIES,
    FILES,
    PLAID_BASE_URL,
    PLAID_CLIENT_ID,
    PLAID_ENV,
    PLAID_SECRET,
    PRODUCTS,
    setup_logger,
)
from flask import Flask, jsonify, render_template, request
from helper_utils import (
    enrich_transaction,
    ensure_directory_exists,
    ensure_file_exists,
    get_available_themes,
    get_current_theme,
    load_json,
    load_transactions_json,
    save_json_with_backup,
    set_theme,
    validate_transaction,
)
from plaid_utils import generate_link_token
from sql_utils import init_db, save_transactions_to_db

logger = setup_logger()

DATA_DIR = DIRECTORIES["DATA_DIR"]
TEMP_DIR = DIRECTORIES["TEMP_DIR"]
LOGS_DIR = DIRECTORIES["LOGS_DIR"]
THEMES_DIR = DIRECTORIES["THEMES_DIR"]
LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
TRANSACTIONS_LIVE = FILES["TRANSACTIONS_LIVE"]
TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]
TRANSACTIONS_RAW_ENRICHED = FILES["TRANSACTIONS_RAW_ENRICHED"]
DEFAULT_THEME = FILES["DEFAULT_THEME"]
CURRENT_THEME = FILES["CURRENT_THEME"]

# Plaid Link & Refresh Functions


def process_access_token(public_token):
    """
    Processes the public token to exchange it for an access token, retrieves
    the item_id and institution_name, and saves them to the relevant files.
    """
    try:
        # Step 1: Exchange public token for access token
        access_token = exchange_public_token(public_token)
        if not access_token:
            return {"error": "Failed to exchange public token for access token."}, 400

        # Step 2: Get item information (item_id and institution_name)
        item_id, institution_name = get_item_info(access_token)
        if not item_id:
            return {"error": "Failed to retrieve item metadata."}, 400

        # Step 3: Save initial account data
        save_initial_account_data(access_token, item_id)

        # Step 4: Save to LinkItems.json
        link_items_file = LINKED_ITEMS
        ensure_file_exists(link_items_file, default_content={})

        with open(link_items_file, "r") as f:
            existing_items = json.load(f)

        existing_items[item_id] = {
            "institution_name": institution_name,
            "item_id": item_id,
            "access_token": access_token,  # Save securely for server-side use
            "linked_at": datetime.now().isoformat(),
        }

        save_json_with_backup(link_items_file, existing_items)
        logger.info(
            f"Saved item_id {item_id} for institution '{institution_name}' to LinkItems.json."
        )

        # Return a success response
        return {
            "message": "Access token processed successfully.",
            "item_id": item_id,
            "institution_name": institution_name,
        }, 200

    except Exception as e:
        logger.error(f"Error processing access token: {str(e)}")
        return {"error": str(e)}, 500


def exchange_public_token(public_token):
    url = f"https://{PLAID_ENV}.plaid.com/item/public_token/exchange"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "public_token": public_token,
    }

    masked_payload = payload.copy()
    masked_payload["client_id"] = "****"
    masked_payload["secret"] = "****"

    logger.info(f"POST {url} with payload: See debug log for payload.")
    logger.debug(f"Payload: {json.dumps(masked_payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            # Save the response to TEMP_DIR
            access_token = save_and_parse_response(
                response, TEMP_DIR / "exchange_response.json"
            ).get("access_token")
            logger.info(f"Access token generated: {access_token}")
            return access_token
        else:
            logger.error(f"Error exchanging token: {response.json()}")
            return None
    except requests.RequestException as re:
        logger.error(f"Request exception during exchange: {str(re)}")
        return None


def save_and_parse_response(response, file_path):
    """
    Save a JSON response to a file and parse it.

    Args:
        response (requests.Response): Response object from an API call.
        file_path (str): Path to save the JSON file.

    Returns:
        dict: Parsed JSON content from the file.
    """
    ensure_directory_exists(os.path.dirname(file_path))

    # Save response JSON to file
    with open(file_path, "w") as temp_file:
        json.dump(response.json(), temp_file, indent=2)
        resolved_path = Path(file_path).resolve()
        logger.debug(f"Saving to {resolved_path}")

    # Parse the saved file
    return load_json(file_path)


def get_item_info(access_token):
    url = f"https://{PLAID_ENV}.plaid.com/item/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        item_data = response.json()
        institution_name = item_data["item"].get(
            "institution_name", "Unknown Institution"
        )
        item_id = item_data["item"].get("item_id")

        ensure_file_exists(LINKED_ITEMS, default_content={})

        with open(LINKED_ITEMS, "r") as f:
            existing_data = json.load(f)

        existing_data[item_id] = {
            "institution_name": institution_name,
            "item_id": item_id,
            "products": item_data["item"].get("products", []),
            "status": item_data.get("status", {}),
        }

        save_json_with_backup(LINKED_ITEMS, existing_data)

        logger.info(
            f"Linked to {institution_name} successfully with item ID: {item_id}"
        )
        return item_id, institution_name
    except Exception as e:
        logger.error(f"Error in get_item_info: {e}")
        return None, None


def save_initial_account_data(access_token, item_id):
    url = f"https://{PLAID_ENV}.plaid.com/accounts/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        account_data = response.json()

        ensure_file_exists(LINKED_ACCOUNTS, default_content={})

        # Merge new account data
        with open(LINKED_ACCOUNTS, "r") as f:
            existing_data = json.load(f)

        for account in account_data["accounts"]:
            account_id = account["account_id"]
            existing_data[account_id] = {
                "item_id": item_id,
                "institution_name": account_data["item"]["institution_name"],
                "access_token": access_token,
                "account_name": account["name"],
                "type": account["type"],
                "subtype": account["subtype"],
                "balances": account.get("balances", {}),
            }

        save_json_with_backup(LINKED_ACCOUNTS, existing_data)

        logger.info(f"Account data saved successfully for item_id {item_id}.")
    except Exception as e:
        logger.error(f"Error in save_initial_account_data: {e}")


# Configure Flask
app = Flask(__name__, template_folder="templates", static_folder="static")


# Main flask app


@app.route("/")
def dashboard():
    """Render the main dashboard."""
    logger.debug("Rendering dashboard.html")
    return render_template("dashboard.html")


# -- Accounts Link and Refresh and Display -- Accounts Managements
@app.route("/accounts", methods=["GET"])
def accounts_page():
    try:
        # Load accounts and items data
        with open(LINKED_ACCOUNTS) as f:
            link_accounts = json.load(f)
        with open(LINKED_ITEMS) as f:
            link_items = json.load(f)

        # Merge relevant details for the page
        accounts_data = []
        for account_id, account in link_accounts.items():
            item_data = link_items.get(account.get("item_id"), {})
            accounts_data.append(
                {
                    "account_id": account_id,
                    "account_name": account.get("account_name"),
                    "institution_name": account.get("institution_name"),
                    "type": account.get("type"),
                    "subtype": account.get("subtype"),
                    "balances": account.get("balances"),
                    "last_successful_update": item_data.get("status", {})
                    .get("transactions", {})
                    .get("last_successful_update"),
                    "products": item_data.get("products", []),
                }
            )

        return render_template("accounts.html", accounts=accounts_data)
    except Exception as e:
        logger.error(f"Error loading accounts page: {e}")
        return render_template("error.html", error="Failed to load accounts data.")


@app.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        logger.info("Fetching account data...")

        # Load LinkedAccounts.json
        try:
            with open(LINKED_ACCOUNTS) as f:
                accounts_data = json.load(f)
            logger.info(
                f"Loaded {len(accounts_data)} accounts from LinkedAccounts.json."
            )
        except FileNotFoundError:
            logger.error("LinkedAccounts.json file not found.")
            return (
                jsonify(
                    {"status": "error", "message": "LinkedAccounts.json not found"}
                ),
                404,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding LinkedAccounts.json: {e}")
            return (
                jsonify(
                    {"status": "error", "message": "Error decoding LinkedAccounts.json"}
                ),
                500,
            )

        # Process account data
        accounts = [
            {
                "id": account_id,
                "name": account_data.get("name", "Unknown Account"),
                "institution": account_data.get(
                    "institution_name", "Unknown Institution"
                ),
                "masked_access_token": f"****{account_id[-4:]}",  # Example masking
                "balances": {
                    "available": account_data.get("balances", {}).get("available"),
                    "current": account_data.get("balances", {}).get("current"),
                },
            }
            for account_id, account_data in accounts_data.items()
        ]
        logger.info(f"Processed {len(accounts)} accounts.")

        return jsonify(accounts), 200

    except Exception as e:
        logger.error(f"Error loading accounts: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/refresh_account", methods=["POST"])
def refresh_account():
    data = request.json
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

    # Load LinkedItems.json
    try:
        with open(LINKED_ITEMS, "r") as f:
            linked_items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.error("LinkedItems.json missing or invalid.")
        return jsonify({"error": "LinkedItems.json not found or invalid."}), 500

    item = linked_items.get(item_id)
    if not item:
        logger.error(f"Item ID {item_id} not found in LinkedItems.json.")
        return jsonify({"error": f"Item ID {item_id} not found."}), 404

    # Determine start_date and end_date
    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    # Load LinkedAccounts.json for access_token
    try:
        with open(LINKED_ACCOUNTS, "r") as f:
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

    # Fetch transactions from Plaid API
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

    # Save transactions to RawTransactions.json
    with open(TRANSACTIONS_RAW, "w") as f:
        json.dump(
            {"transactions": transactions_data.get("transactions", [])}, f, indent=4
        )
    logger.info(
        f"Saved {len(transactions_data.get('transactions', []))} transactions to {TRANSACTIONS_RAW}."
    )

    # Update balances in LinkAccounts.json
    for account in transactions_data.get("accounts", []):
        account_id = account["account_id"]
        if account_id in linked_accounts:
            linked_accounts[account_id]["balances"] = account["balances"]

    with open(LINKED_ACCOUNTS, "w") as f:
        json.dump(linked_accounts, f, indent=4)

    # Update last_successful_update in LinkedItems.json
    item["status"]["transactions"][
        "last_successful_update"
    ] = datetime.now().isoformat()
    linked_items[item_id] = item
    with open(LINKED_ITEMS, "w") as f:
        json.dump(linked_items, f, indent=4)

    # Save transactions to the database
    save_transactions_to_db(transactions_data.get("transactions", []), linked_accounts)

    # Log before processing transactions
    logger.info("Calling process_transactions() to update live transactions...")
    process_transactions()
    logger.info("process_transactions() completed.")

    logger.info(
        f"Refreshed account {item_id}. Fetched and saved {len(transactions_data.get('transactions', []))} transactions."
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


@app.route("/save_group", methods=["POST"])
def save_group():
    try:
        data = request.json
        group_name = data.get("groupName")
        account_ids = data.get("accountIds")

        if not group_name or not account_ids:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Group name and accounts are required.",
                    }
                ),
                400,
            )

        # Example: Save the group data to a file or database
        group_data = {"name": group_name, "accounts": account_ids}
        with open("groups.json", "a") as f:
            f.write(json.dumps(group_data) + "\n")

        return (
            jsonify({"status": "success", "message": "Group saved successfully!"}),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Link token routes
@app.route("/save_public_token", methods=["POST"])
def save_public_token():
    try:
        if not request.is_json:
            logger.error("Invalid request: Content-Type must be application/json")
            return (
                jsonify({"error": "Invalid Content-Type. Must be application/json."}),
                400,
            )

        data = request.get_json()
        logger.debug(f"Received POST data: {json.dumps(data, indent=2)}")

        public_token = data.get("public_token")
        if public_token:
            ensure_directory_exists(TEMP_DIR)  # Ensure the directory exists

            with open(os.path.join(TEMP_DIR, "public_token.txt"), "w") as f:
                f.write(public_token)
            logger.info("Public token saved to file")

            # Exchange the public token for an access token
            access_token = exchange_public_token(public_token)
            if access_token:
                # Get item metadata
                item_id, institution_name = get_item_info(access_token)
                if item_id:
                    # Get and save initial account data
                    save_initial_account_data(access_token, item_id)
                    logger.info(
                        f"Linked to {institution_name} successfully with item ID: {item_id}"
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
                    logger.error("Failed to retrieve item metadata")
                    return jsonify({"error": "Failed to retrieve item metadata"}), 400

            else:
                logger.error("No public token provided")
                return jsonify({"error": "No public token provided"}), 400
    except json.JSONDecodeError as jde:
        logger.error(f"JSON decode error: {str(jde)}")
        return jsonify({"error": "Invalid JSON payload", "details": str(jde)}), 400
    except Exception as e:
        logger.error(f"Error processing public token: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Server error while processing public token",
                    "details": str(e),
                }
            ),
            500,
        )


@app.route("/get_link_token", methods=["GET"])
def get_link_token():
    products_param = request.args.get("products")
    products = products_param.split(",") if products_param else PRODUCTS

    logger.debug(f"Generating link token for products: {products}")
    link_token = generate_link_token(products)
    if link_token:
        logger.info(f"Successfully generated link token with products: {products}")
        return jsonify({"link_token": link_token})
    else:
        logger.error("Failed to create link token")
        return jsonify({"error": "Failed to create link token"}), 400


# Get institution level aggregate view
@app.route("/get_institutions", methods=["GET"])
def get_institutions():
    try:
        logger.info("Fetching institutions and accounts data...")

        # Load LinkedItems.json
        try:
            with open(LINKED_ITEMS) as f:
                link_items = json.load(f)
            logger.info(f"Loaded {len(link_items)} items from LinkedItems.json.")
        except FileNotFoundError:
            logger.error("LinkedItems.json file not found.")
            return (
                jsonify({"status": "error", "message": "LinkedItems.json not found"}),
                404,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding LinkedItems.json: {e}")
            return (
                jsonify(
                    {"status": "error", "message": "Error decoding LinkedItems.json"}
                ),
                500,
            )

        # Load LinkedAccounts.json
        try:
            with open(LINKED_ACCOUNTS) as f:
                link_accounts = json.load(f)
            logger.info(
                f"Loaded {len(link_accounts)} accounts from LinkedAccounts.json."
            )
        except FileNotFoundError:
            logger.error("LinkedAccounts.json file not found.")
            return (
                jsonify(
                    {"status": "error", "message": "LinkedAccounts.json not found"}
                ),
                404,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding LinkedAccounts.json: {e}")
            return (
                jsonify(
                    {"status": "error", "message": "Error decoding LinkedAccounts.json"}
                ),
                500,
            )

        # Aggregate data by institution
        logger.info("Aggregating data by institution...")
        institutions = {}

        for item_id, item_data in link_items.items():
            institution_name = item_data.get("institution_name", "Unknown Institution")
            last_successful_update = (
                item_data.get("status", {})
                .get("transactions", {})
                .get("last_successful_update")
            )

            # Set "Never refreshed" if last_successful_update is null or empty
            last_successful_update = last_successful_update or "Never refreshed"

            if institution_name not in institutions:
                institutions[institution_name] = {
                    "item_id": item_id,
                    "products": item_data.get("products", []),
                    "status": item_data.get("status", {}),
                    "accounts": [],
                    "last_successful_update": last_successful_update,  # Per institution
                }
                logger.debug(
                    f"Added institution: {institution_name} with last refresh: {last_successful_update}"
                )

            # Link accounts to institutions with balance adjustment for liabilities
            linked_accounts = []
            for account_id, account_data in link_accounts.items():
                if account_data.get("item_id") == item_id:
                    balance = account_data.get("balances", {}).get("current", 0)
                    if account_data.get("type") == "credit":
                        balance *= -1  # Negate balance for liabilities

                    linked_accounts.append(
                        {
                            "account_id": account_id,
                            "account_name": account_data.get(
                                "account_name", "Unknown Account"
                            ),
                            "type": account_data.get("type", "Unknown"),
                            "subtype": account_data.get("subtype", "Unknown"),
                            "balances": {"current": balance},
                        }
                    )

            institutions[institution_name]["accounts"].extend(linked_accounts)
            logger.debug(
                f"{len(linked_accounts)} accounts linked to {institution_name}"
            )

        logger.info("Returning aggregated institution data.")
        return (
            jsonify(
                {
                    "status": "success",
                    "institutions": institutions,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error fetching institutions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Transaction handling routes
@app.route("/transactions", methods=["GET"])
def transactions_page():
    try:
        transactions = load_transactions_json(TRANSACTIONS_LIVE)
        formatted_transactions = [
            {
                "date": datetime.strptime(tx["date"], "%Y-%m-%d").strftime("%b %d, %Y"),
                "name": tx.get("name", "N/A"),
                "amount": f"${abs(tx['amount']):,.2f}"
                if tx["amount"] < 0
                else f"${tx['amount']:,.2f}",
                "category": tx.get("category", ["Uncategorized"]),
                "merchant_name": tx.get("merchant_name", "Unknown"),
                "account_name": tx.get("account_name", "Unknown Account"),
                "institution_name": tx.get("institution_name", "Unknown Institution"),
            }
            for tx in transactions
        ]
        return render_template("transactions.html", transactions=formatted_transactions)

    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        return jsonify({"error": f"File not found: {str(e)}"}), 404
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {str(e)}")
        return jsonify({"error": f"Invalid JSON format: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500


@app.route("/get_transactions", methods=["GET"])
def load_transactions():
    try:
        # Load live transactions
        transactions = load_transactions_json(TRANSACTIONS_LIVE)
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))
        start = (page - 1) * page_size
        end = start + page_size
        paginated_transactions = transactions[start:end]

        return jsonify(
            {"transactions": paginated_transactions, "total": len(transactions)}
        )
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        return jsonify({"transactions": [], "total": 0}), 500


@app.route("/process_transactions", methods=["POST"])
def process_transactions():
    """Processes raw transactions, enriches them, and updates live data."""

    # Load raw transactions into memory buffer
    transactions = load_transactions_json(TRANSACTIONS_RAW)
    logger.debug(f"Loaded {len(transactions)} raw transactions.")

    # Load accounts and items
    try:
        accounts = load_json(LINKED_ACCOUNTS)
        items = load_json(LINKED_ITEMS)
        logger.debug(f"Loaded {len(accounts)} accounts, {len(items)} items.")
    except Exception as e:
        logger.error(f"Error loading accounts or items: {e}")
        return jsonify({"error": "Failed to load accounts or items."}), 500

    # Process transactions in-memory buffer
    enriched_transactions = []
    for tx in transactions:
        if not validate_transaction(tx):
            logger.warning(f"Skipping invalid transaction: {tx}")
            continue

        try:
            enriched_tx = enrich_transaction(tx, accounts, items)
            enriched_transactions.append(enriched_tx)
            logger.debug(f"Enriched transaction: {enriched_tx}")
        except Exception as e:
            logger.error(f"Error enriching transaction: {tx}, error: {e}")

    logger.info(f"Enriched {len(enriched_transactions)} transactions.")

    # Load existing transactions into memory (small buffer)
    existing_transactions = load_transactions_json(TRANSACTIONS_LIVE)
    logger.debug(
        f"Loaded {len(existing_transactions)} existing transactions from TRANSACTIONS_LIVE."
    )

    # Deduplicate transactions in-memory (no extra file writes)
    unique_transactions = {
        tx["transaction_id"]: tx for tx in existing_transactions + enriched_transactions
    }

    # Save final transactions **once** instead of multiple times
    save_json_with_backup(
        TRANSACTIONS_LIVE, {"transactions": list(unique_transactions.values())}
    )
    logger.info(
        f"Updated TRANSACTIONS_LIVE with {len(unique_transactions)} transactions."
    )

    return (
        jsonify(
            {"status": "success", "message": "Transactions processed successfully."}
        ),
        200,
    )


@app.route("/api/category_breakdown", methods=["GET"])
def get_category_breakdown():
    try:
        transactions = load_json(TRANSACTIONS_LIVE).get("transactions", [])

        category_data = {}
        for tx in transactions:
            category = tx.get("category", ["Uncategorized"])
            if (
                isinstance(category, list) and category
            ):  # Ensure it's a list and not empty
                category = category[0]  # Use the first category

            amount = tx.get("amount")
            if amount is not None and isinstance(amount, (int, float)) and amount < 0:
                category_data[category] = category_data.get(category, 0) + abs(amount)

        category_breakdown = [
            {"category": cat, "amount": round(amt, 2)}
            for cat, amt in category_data.items()
        ]

        return jsonify({"status": "success", "data": category_breakdown}), 200

    except FileNotFoundError:
        logger.error("TRANSACTIONS_LIVE file not found.")
        return (
            jsonify({"status": "error", "message": "Transactions file not found."}),
            404,
        )

    except json.JSONDecodeError:
        logger.error("Error decoding TRANSACTIONS_LIVE.")
        return (
            jsonify(
                {"status": "error", "message": "Invalid transactions file format."}
            ),
            400,
        )

    except Exception as e:
        logger.error(f"Error in category breakdown: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Main Dashboard Visuals
@app.route("/api/cash_flow", methods=["GET"])
def get_cash_flow():
    try:
        # Load transactions from the JSON file
        transactions = load_json(TRANSACTIONS_LIVE).get("transactions", [])

        # Aggregate income and expenses by month
        monthly_cash_flow = {}
        for tx in transactions:
            try:
                date = datetime.strptime(tx["date"], "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Skipping transaction with invalid date: {tx}")
                continue

            month_year = f"{date.strftime('%B')} {date.year}"
            if month_year not in monthly_cash_flow:
                monthly_cash_flow[month_year] = {"income": 0, "expenses": 0}

            if "amount" not in tx or not isinstance(tx["amount"], (int, float)):
                logger.warning(f"Skipping invalid transaction: {tx}")
                continue

            if tx["amount"] > 0:
                monthly_cash_flow[month_year]["income"] += tx["amount"]
            else:
                monthly_cash_flow[month_year]["expenses"] += abs(tx["amount"])

        # Prepare data for the frontend
        data = [
            {"month": month, **values}
            for month, values in sorted(
                monthly_cash_flow.items(),
                key=lambda x: datetime.strptime(x[0], "%B %Y"),
            )
        ]

        # Calculate total income and expenses (optional metadata for analytics)
        total_income = sum(values["income"] for values in monthly_cash_flow.values())
        total_expenses = sum(
            values["expenses"] for values in monthly_cash_flow.values()
        )

        return jsonify(
            {
                "status": "success",
                "data": data,
                "metadata": {
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "total_transactions": len(transactions),
                },
            }
        )

    except FileNotFoundError:
        logger.error("TRANSACTIONS_LIVE file not found.")
        return (
            jsonify({"status": "error", "message": "Transactions file not found."}),
            404,
        )

    except json.JSONDecodeError:
        logger.error("Error decoding TRANSACTIONS_LIVE.")
        return (
            jsonify(
                {"status": "error", "message": "Invalid transactions file format."}
            ),
            400,
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/net_worth", methods=["GET"])
def get_net_worth():
    """
    Mock endpoint to return net worth data. This example:
    1. Reads the 'balances' from LinkedAccounts.json.
    2. Sums all current balances (treating credit accounts as negative if needed).
    3. Generates a small monthly timeseries for the past 6 months + current.
    """
    try:
        # 1. Load accounts data
        with open(LINKED_ACCOUNTS, "r") as f:
            linked_accounts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.error("LinkedAccounts.json missing or invalid.")
        return jsonify({"status": "error", "message": "No accounts found."}), 404

    # 2. Calculate the most recent net worth by summing all 'current' balances.
    #    If you'd like to treat credit card balances as negative, you can do so.
    current_net_worth = 0
    for account_id, account_data in linked_accounts.items():
        bal = account_data.get("balances", {}).get("current", 0)
        # If it is a credit account, we can treat it as liability by negating.
        if account_data.get("type") == "credit":
            bal *= -1
        current_net_worth += bal

    # 3. Generate a timeseries of net worth for the last 6 months, plus this month.
    #    For demo, we start from (current_net_worth - some random offset) and move forward.
    data = []
    base_date = datetime.now().replace(day=1)
    running_value = current_net_worth - random.randint(500, 5000)  # example baseline

    for months_ago in range(6, -1, -1):
        date_obj = base_date - timedelta(days=30 * months_ago)
        variation = random.randint(-2000, 3000)
        running_value += variation
        # If it's the final iteration (this month), set net worth to the actual current_net_worth
        if months_ago == 0:
            running_value = current_net_worth
        data.append(
            {"date": date_obj.strftime("%Y-%m-%d"), "netWorth": round(running_value, 2)}
        )

    return jsonify({"status": "success", "data": data}), 200


# --- Route for settings and themes
@app.route("/settings")
def settings():
    """Render the settings page for selecting themes."""
    return render_template("settings.html")


# Endpoint to fetch themes
@app.route("/themes", methods=["GET"])
def fetch_themes():
    """Fetch available themes and the current theme."""
    try:
        themes = get_available_themes()
        current_theme = get_current_theme()
        return jsonify({"themes": themes, "current_theme": current_theme}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_theme", methods=["POST"])
def change_theme():
    """Set a new theme."""
    data = request.json
    theme_name = data.get("theme")

    if not theme_name:
        return jsonify({"error": "No theme provided"}), 400

    try:
        if set_theme(theme_name):
            return jsonify({"success": True, "theme": theme_name}), 200
        else:
            return jsonify({"error": "Failed to set theme"}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@app.context_processor
def inject_theme():
    """Inject the current theme into the template context."""
    return {"current_theme": get_current_theme()}


# Debugging route
@app.route("/debug")
def debug():
    """Debugging information."""
    return jsonify(
        {
            "current_working_directory": str(Path.cwd()),
            "template_folder": app.template_folder,
            "static_folder": app.static_folder,
            "themes_directory": str(THEMES_DIR.resolve()),
            "data_directory": str(DATA_DIR.resolve()),
            "temp_directory": str(TEMP_DIR.resolve()),
        }
    )


if __name__ == "__main__":
    logger.info("Starting Flask application, initializing SQL Database.")
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
