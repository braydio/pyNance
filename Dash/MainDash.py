import json
import os
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
    logger,
)
from flask import Flask, jsonify, render_template, request
from plaid_utils import generate_link_token
from sql_utils import init_db, save_transactions_to_db

DATA_DIR = DIRECTORIES["DATA_DIR"]
TEMP_DIR = DIRECTORIES["TEMP_DIR"]
LOGS_DIR = DIRECTORIES["LOGS_DIR"]
THEMES_DIR = DIRECTORIES["THEMES_DIR"]
LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
DEFAULT_THEME = FILES["DEFAULT_THEME"]
CURRENT_THEME = FILES["CURRENT_THEME"]


# Utility to get available themes
def get_available_themes():
    try:
        themes = [f.name for f in THEMES_DIR.glob("*.css")]
        logger.debug(f"Available themes: {themes}")
        return themes
    except Exception as e:
        logger.error(f"Error accessing themes directory: {e}")
        return []


# Misc utility functions
def load_json(file_path):
    """Load data from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            resolved_path = Path(file_path).resolve()
            logger.debug(f"Loaded from {resolved_path}")
            return json.load(f)
    return {}


def save_json_with_backup(file_path, data):
    try:
        backup_path = f"{file_path}.bak"

        # Create a backup of the existing file, if it exists
        if os.path.exists(file_path):
            if os.path.exists(backup_path):
                logger.info(f"Overwriting stale backup: {backup_path}")
                os.remove(backup_path)
            os.rename(file_path, backup_path)

        # Save the new JSON data to the file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        logger.info(
            f"Data successfully saved to {file_path}. Backup created at {backup_path}."
        )

    except OSError as e:
        logger.error(f"File operation failed: {e}")
        raise e

    except json.JSONDecodeError as e:
        logger.error(f"JSON encoding error: {e}")
        raise e

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise e


def ensure_directory_exists(directory_path):
    """
    Ensures that the given directory exists. Creates it if it doesn't.

    Args:
        directory_path (str): Path to the directory.
    """
    os.makedirs(directory_path, exist_ok=True)


def ensure_file_exists(file_path, default_content=None):
    """
    Ensures that the given file exists. Creates it if it doesn't, with optional default content.

    Args:
        file_path (str): Path to the file.
        default_content (str, dict, list, optional): Content to write to the file if it's created. Default is None.
    """
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            if default_content is not None:
                if isinstance(default_content, (dict, list)):
                    import json

                    json.dump(default_content, file, indent=2)
                else:
                    file.write(default_content)
            else:
                file.write("")


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


@app.route("/link_session")
def link_status():
    """Check the current status of the link session."""
    session_file = TEMP_DIR / "link_session.json"
    try:
        with session_file.open("r") as f:
            session_data = json.load(f)
        logger.debug(f"Link session data: {session_data}")
        return jsonify(session_data), 200
    except FileNotFoundError:
        logger.warning(f"Link session file not found: {session_file}")
        return jsonify({"status": "no_session"}), 404


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


# Account displays on /accounts route
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


# Refresh account with access token
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
    last_update = (
        item.get("status", {}).get("transactions", {}).get("last_successful_update")
    )
    start_date = (
        last_update.split("T")[0]
        if last_update
        else (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    )
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
        transactions = transactions_data.get("transactions", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Plaid API error: {str(e)}")
        return jsonify({"error": f"Failed to fetch transactions: {str(e)}"}), 500

    # Update last_successful_update in LinkedItems.json
    item["status"]["transactions"][
        "last_successful_update"
    ] = datetime.now().isoformat()
    linked_items[item_id] = item
    with open(LINKED_ITEMS, "w") as f:
        json.dump(linked_items, f, indent=4)

    # Save transactions to the database
    save_transactions_to_db(transactions, linked_accounts)

    # Save transactions to a JSON file
    latest_transactions_file = FILES["LATEST_TRANSACTIONS"]
    with open(latest_transactions_file, "w") as f:
        json.dump(transactions_data, f, indent=4)

    logger.info(
        f"Refreshed account {item_id}. Fetched and saved {len(transactions)} transactions."
    )
    return (
        jsonify({"status": "success", "transactions_fetched": len(transactions)}),
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


@app.route("/transactions", methods=["GET"])
def transactions_page():
    try:
        # Load transactions, accounts, and items data
        with open("Dash/data/Transactions.json") as tf:
            transactions_data = json.load(tf)
        with open(LINKED_ACCOUNTS) as af:
            link_accounts = json.load(af)
        with open(LINKED_ITEMS) as lf:
            link_items = json.load(lf)

        # Enrich transactions with account and item details
        enriched_transactions = []
        for transaction in transactions_data.get("transactions", []):
            account_id = transaction["account_id"]
            account_info = link_accounts.get(account_id, {})
            item_info = link_items.get(account_info.get("item_id", ""), {})

            enriched_transactions.append(
                {
                    "date": transaction["date"],
                    "name": transaction["name"],
                    "amount": transaction["amount"],
                    "category": transaction.get("category", ["Unknown"])[-1],
                    "merchant_name": transaction.get("merchant_name", "Unknown"),
                    "institution_name": account_info.get("institution_name", "Unknown"),
                    "account_name": account_info.get("account_name", "Unknown Account"),
                    "account_type": account_info.get("type", "Unknown"),
                    "account_subtype": account_info.get("subtype", "Unknown"),
                    "last_successful_update": item_info.get("status", {})
                    .get("transactions", {})
                    .get("last_successful_update", "N/A"),
                }
            )

        return render_template("transactions.html", transactions=enriched_transactions)
    except Exception as e:
        logger.error(f"Error loading transactions page: {e}")
        return render_template("error.html", error="Failed to load transactions data.")


# Main Dashboard Visuals
@app.route("/api/cash_flow", methods=["GET"])
def get_cash_flow():
    """Placeholder for cash flow data."""
    # Mock data for demonstration
    cash_flow_data = {
        "status": "success",
        "data": [
            {"month": "January 2025", "income": 4500.00, "expenses": 3200.00},
            {"month": "February 2025", "income": 4700.00, "expenses": 3400.00},
            {"month": "March 2025", "income": 4800.00, "expenses": 3500.00},
            {"month": "April 2025", "income": 4900.00, "expenses": 3600.00},
        ],
    }
    return jsonify(cash_flow_data)


# --- Route for settings.html
@app.route("/settings")
def settings():
    """Render the settings page for selecting themes."""
    return render_template("settings.html")


# Endpoint to fetch themes
@app.route("/themes", methods=["GET"])
def fetch_themes():
    """Fetch available themes and the current theme."""
    themes = get_available_themes()
    current_theme_file = CURRENT_THEME
    default_theme_string = str(DEFAULT_THEME)
    try:
        current_theme = current_theme_file.read_text().strip()
        logger.debug(f"Current active theme: {default_theme_string}")
    except FileNotFoundError:
        logger.debug(
            f"{current_theme_file} not found, defaulting to {default_theme_string}"
        )
        current_theme = default_theme_string

    if themes:
        logger.debug(f"Found themes at {current_theme_file}")
        return jsonify({"themes": themes, "current_theme": current_theme}), 200
    else:
        return (
            jsonify({"error": "No themes available", "current_theme": current_theme}),
            404,
        )


@app.route("/set_theme", methods=["POST"])
def set_theme():
    """Set the selected theme."""
    data = request.json
    selected_theme = data.get("theme")

    if not selected_theme:
        return jsonify({"error": "No theme provided"}), 400

    if selected_theme not in get_available_themes():
        return jsonify({"error": f"Theme '{selected_theme}' not found"}), 404

    current_theme_file = CURRENT_THEME
    try:
        current_theme_file.write_text(selected_theme)
        logger.debug(f"Theme updated to: {selected_theme}")
        return jsonify({"success": True, "theme": selected_theme}), 200
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return jsonify({"error": str(e)}), 500


@app.context_processor
def inject_theme():
    """
    Determines the current theme to use based on the following order:
    1. A user-specified theme in the CURRENT_THEME file.
    2. A page-specific theme (e.g., 'dashboard.css').
    3. The default theme ('default.css').

    Returns:
        dict: A dictionary containing the 'current_theme' key.
    """
    try:
        # Step 1: Attempt to read the user-specified theme
        if CURRENT_THEME.exists():
            with open(CURRENT_THEME, "r") as f:
                current_theme = f.read().strip()
            theme_path = THEMES_DIR / current_theme
            if theme_path.exists():
                return {"current_theme": current_theme}

        # Step 2: Determine the page-specific theme
        current_page = request.path.split("/")[-1] or "dashboard"
        page_name = current_page.split(".")[0]  # Extract base name (e.g., 'dashboard')
        page_theme = f"{page_name}.css"
        page_theme_path = THEMES_DIR / page_theme

        if page_theme_path.exists():
            return {"current_theme": page_theme}

        # Step 3: Fallback to the default theme
        return {"current_theme": DEFAULT_THEME.name}

    except Exception as e:
        logger.error(f"Error determining theme: {e}")
        return {"current_theme": DEFAULT_THEME.name}


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
