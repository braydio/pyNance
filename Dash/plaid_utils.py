import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests
from config import (
    DIRECTORIES,
    FILES,
    PLAID_BASE_URL,
    PLAID_CLIENT_ID,
    PLAID_ENV,
    PLAID_SECRET,
    setup_logger,
)
from flask import Blueprint, jsonify, request
from helper_utils import (
    ensure_directory_exists,
    ensure_file_exists,
    load_json,
    save_json_with_backup,
)
from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.configuration import Configuration
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from sql_utils import (
    save_account_balances,
    save_accounts_to_db,
    save_initial_db,
    save_recent_refresh_to_db,
    save_transactions_to_db,
)

logger = setup_logger()
TEMP_DIR = DIRECTORIES["TEMP_DIR"]
LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]

plaid = Blueprint("plaid", __name__)


@plaid.route("/save_public_token", methods=["POST"])
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
            ensure_directory_exists(TEMP_DIR)
            with open(os.path.join(TEMP_DIR, "public_token.txt"), "w") as f:
                f.write(public_token)
            logger.info("Public token saved to file")

            access_token = exchange_public_token(public_token)
            if access_token:
                item_id, institution_name = get_item_info(access_token)
                if item_id:
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


@plaid.route("/transactions_refresh", methods=["POST"])
def refresh_account():
    data = request.json
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

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

    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

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

    with open(TRANSACTIONS_RAW, "w") as f:
        json.dump(
            {"transactions": transactions_data.get("transactions", [])}, f, indent=4
        )
    logger.info(
        f"Saved {len(transactions_data.get('transactions', []))} transactions to {TRANSACTIONS_RAW}."
    )

    for account in transactions_data.get("accounts", []):
        account_id = account["account_id"]
        if account_id in linked_accounts:
            linked_accounts[account_id]["balances"] = account["balances"]

    with open(LINKED_ACCOUNTS, "w") as f:
        json.dump(linked_accounts, f, indent=4)

    # Ensure nested structure exists before updating timestamp.
    if "transactions" not in item.get("status", {}):
        item.setdefault("status", {})["transactions"] = {}
    item["status"]["transactions"][
        "last_successful_update"
    ] = datetime.now().isoformat()
    linked_items[item_id] = item
    with open(LINKED_ITEMS, "w") as f:
        json.dump(linked_items, f, indent=4)

    save_transactions_to_db(transactions_data.get("transactions", []), linked_accounts)
    total_transactions = len(transactions_data.get("transactions", []))
    save_recent_refresh_to_db(
        item_id=item_id,
        start_date=start_date,
        end_date=end_date,
        total_transactions=total_transactions,
        raw_data=transactions_data,
    )
    logger.info("Saved recent refresh details to the database.")

    # process_transactions()
    logger.info(
        f"Refreshed account {item_id}. Fetched and saved {total_transactions} transactions."
    )
    return (
        jsonify({"status": "success", "transactions_fetched": total_transactions}),
        200,
    )


def generate_link_token(products_list):
    logger.debug(f"Current Working Dir: {os.getcwd()}")

    # Configure Plaid API client
    configuration = Configuration(
        host=f"https://{PLAID_ENV}.plaid.com",
        api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET},
    )
    logger.debug(f"Configuration: {configuration}")

    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    logger.debug("Plaid API client configured")

    # Convert product strings to Products() objects
    products = [Products(product) for product in products_list]
    logger.debug(f"Products: {products}")

    # Build request
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="user-unique-id"),
        client_name="My Finance Dashboard",
        products=products,
        country_codes=[CountryCode("US")],
        language="en",
        webhook="https://sample-web-hook.com",
        redirect_uri="https://localhost/callback",
    )
    logger.debug(f"LinkTokenCreateRequest: {request}")

    # Create link token
    try:
        response = client.link_token_create(request)
        link_token = response["link_token"]
        logger.info(f"Link token created: {link_token}")
        return link_token
    except Exception as e:
        logger.error(f"Error creating link token: {e}")
        return None


def process_access_token(public_token):
    try:
        access_token = exchange_public_token(public_token)
        if not access_token:
            return {"error": "Failed to exchange public token for access token."}, 400

        item_id, institution_name = get_item_info(access_token)
        if not item_id:
            return {"error": "Failed to retrieve item metadata."}, 400

        save_initial_account_data(access_token, item_id)

        ensure_file_exists(LINKED_ITEMS, default_content={})
        with open(LINKED_ITEMS, "r") as f:
            existing_items = json.load(f)

        existing_items[item_id] = {
            "institution_name": institution_name,
            "item_id": item_id,
            "access_token": access_token,
            "linked_at": datetime.now().isoformat(),
            "status": {},
        }

        save_json_with_backup(LINKED_ITEMS, existing_items)
        logger.info(f"Saved item_id {item_id} for institution '{institution_name}'.")

        save_initial_db()

        return {
            "message": "Access token processed successfully.",
            "item_id": item_id,
            "institution_name": institution_name,
        }, 200

    except Exception as e:
        logger.error(f"Error processing access token: {e}")
        return {"error": str(e)}, 500


def save_and_parse_response(response, file_path):
    ensure_directory_exists(os.path.dirname(file_path))
    with open(file_path, "w") as temp_file:
        json.dump(response.json(), temp_file, indent=2)
    resolved_path = Path(file_path).resolve()
    logger.debug(f"Saved response to {resolved_path}")
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
        logger.info(f"Linked to {institution_name} with item ID: {item_id}")
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
        with open(LINKED_ACCOUNTS, "r") as f:
            existing_data = json.load(f)
        for account in account_data["accounts"]:
            account_id = account["account_id"]
            existing_data[account_id] = {
                "item_id": item_id,
                "institution_name": account_data["item"].get(
                    "institution_name", "Unknown Institution"
                ),
                "access_token": access_token,
                "account_name": account["name"],
                "type": account["type"],
                "subtype": account["subtype"],
                "balances": account.get("balances", {}),
            }
        save_json_with_backup(LINKED_ACCOUNTS, existing_data)
        save_accounts_to_db(account_data["accounts"], item_id)
        save_account_balances(account_data["accounts"])
        logger.info(f"Account data saved for item_id {item_id}.")
    except Exception as e:
        logger.error(f"Error in save_initial_account_data: {e}")


LINKED_INVESTMENTS = os.path.join(TEMP_DIR, "LinkedInvestments.json")
LINKED_INVESTMENT_ACCOUNTS = os.path.join(TEMP_DIR, "LinkedInvestmentAccounts.json")
INVESTMENTS_RAW = os.path.join(TEMP_DIR, "investments_raw.json")

# Create a Blueprint for investments endpoints
plaid_investments = Blueprint("plaid_investments", __name__)

# ------------------------------------------------------------------------------
# Module: Saving Investments Public Token
# ------------------------------------------------------------------------------


@plaid_investments.route("/save_investments_public_token", methods=["POST"])
def save_investments_public_token():
    """
    Endpoint to save the public token for an investments item,
    exchange it for an access token, and save initial account data.
    """
    try:
        if not request.is_json:
            logger.error("Invalid request: Content-Type must be application/json")
            return (
                jsonify({"error": "Invalid Content-Type. Must be application/json."}),
                400,
            )

        data = request.get_json()
        logger.debug(
            f"Received POST data for investments: {json.dumps(data, indent=2)}"
        )
        public_token = data.get("public_token")
        if public_token:
            ensure_directory_exists(TEMP_DIR)
            with open(os.path.join(TEMP_DIR, "investments_public_token.txt"), "w") as f:
                f.write(public_token)
            logger.info("Investments public token saved to file")

            access_token = exchange_public_token(public_token)
            if access_token:
                item_id, institution_name = get_investments_item_info(access_token)
                if item_id:
                    save_initial_investments_data(access_token, item_id)
                    logger.info(
                        f"Linked investments item for {institution_name} successfully with item ID: {item_id}"
                    )
                    # Save the investments item into a JSON file
                    ensure_file_exists(LINKED_INVESTMENTS, default_content={})
                    try:
                        with open(LINKED_INVESTMENTS, "r") as f:
                            linked_items = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        linked_items = {}

                    linked_items[item_id] = {
                        "institution_name": institution_name,
                        "item_id": item_id,
                        "access_token": access_token,
                        "linked_at": datetime.now().isoformat(),
                        "status": {},
                    }
                    save_json_with_backup(LINKED_INVESTMENTS, linked_items)

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
                    logger.error("Failed to retrieve investments item metadata")
                    return (
                        jsonify(
                            {"error": "Failed to retrieve investments item metadata"}
                        ),
                        400,
                    )
            else:
                logger.error("No public token provided")
                return jsonify({"error": "No public token provided"}), 400

    except json.JSONDecodeError as jde:
        logger.error(f"JSON decode error: {str(jde)}")
        return jsonify({"error": "Invalid JSON payload", "details": str(jde)}), 400
    except Exception as e:
        logger.error(f"Error processing investments public token: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Server error while processing investments public token",
                    "details": str(e),
                }
            ),
            500,
        )


# ------------------------------------------------------------------------------
# Module: Refreshing Investments Data
# ------------------------------------------------------------------------------


@plaid_investments.route("/investments_refresh", methods=["POST"])
def refresh_investments():
    """
    Endpoint to refresh investments holdings data.
    It looks up the investments item by item_id and fetches updated holdings.
    """
    data = request.get_json()
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

    # Load linked investments items
    try:
        with open(LINKED_INVESTMENTS, "r") as f:
            linked_items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.error("LinkedInvestments.json missing or invalid.")
        return jsonify({"error": "LinkedInvestments.json not found or invalid."}), 500

    item = linked_items.get(item_id)
    if not item:
        logger.error(
            f"Investments item ID {item_id} not found in LinkedInvestments.json."
        )
        return jsonify({"error": f"Item ID {item_id} not found."}), 404

    # For investments, the refresh might not require a date range, but adjust as needed
    access_token = item.get("access_token")
    if not access_token:
        logger.error(f"No access token found for investments item ID {item_id}.")
        return jsonify({"error": f"No access token for item ID {item_id}."}), 400

    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    url = f"https://{PLAID_BASE_URL}/investments/holdings/get"

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        investments_data = response.json()
        logger.debug(f"Plaid Investments API response: {investments_data}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Plaid Investments API error: {str(e)}")
        return jsonify({"error": f"Failed to fetch investments data: {str(e)}"}), 500

    # Save raw investments data for auditing or debugging
    with open(INVESTMENTS_RAW, "w") as f:
        json.dump(investments_data, f, indent=4)
    logger.info(f"Saved investments data to {INVESTMENTS_RAW}.")

    # Update linked investments item with a timestamp for refresh status
    if "holdings" not in item.get("status", {}):
        item.setdefault("status", {})["holdings"] = {}
    item["status"]["holdings"]["last_successful_update"] = datetime.now().isoformat()
    linked_items[item_id] = item
    save_json_with_backup(LINKED_INVESTMENTS, linked_items)

    # (Optional) Save investments account/holdings details to a separate file or database
    ensure_file_exists(LINKED_INVESTMENT_ACCOUNTS, default_content={})
    try:
        with open(LINKED_INVESTMENT_ACCOUNTS, "r") as f:
            investment_accounts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        investment_accounts = {}

    # Assume investments_data includes a list of "accounts" or "holdings"
    for holding in investments_data.get("holdings", []):
        account_id = holding.get("account_id")
        investment_accounts[account_id] = holding

    save_json_with_backup(LINKED_INVESTMENT_ACCOUNTS, investment_accounts)

    # (Optional) Process and save investments data to your database here
    # process_investments_holdings(investments_data.get("holdings", []))

    total_holdings = len(investments_data.get("holdings", []))
    logger.info(
        f"Refreshed investments item {item_id}. Fetched and saved {total_holdings} holdings."
    )

    return jsonify({"status": "success", "holdings_fetched": total_holdings}), 200


# ------------------------------------------------------------------------------
# Helper: Get Investments Item Info
# ------------------------------------------------------------------------------


def get_investments_item_info(access_token):
    """
    Retrieve investments item info using the /item/get endpoint.
    (Depending on your Plaid configuration, investments info might be similar to transactions.)
    """
    url = f"https://{PLAID_BASE_URL}/item/get"
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
        logger.info(f"Retrieved investments item info: {institution_name}, {item_id}")
        return item_id, institution_name
    except Exception as e:
        logger.error(f"Error retrieving investments item info: {e}")
        return None, None


# ------------------------------------------------------------------------------
# Helper: Save Initial Investments Data
# ------------------------------------------------------------------------------


def save_initial_investments_data(access_token, item_id):
    """
    Save the initial investments account/holdings data when the investments item is linked.
    This uses the /investments/holdings/get endpoint.
    """
    url = f"https://{PLAID_BASE_URL}/investments/holdings/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        investments_data = response.json()
        # Save the initial data locally (or to your DB)
        ensure_file_exists(LINKED_INVESTMENT_ACCOUNTS, default_content={})
        try:
            with open(LINKED_INVESTMENT_ACCOUNTS, "r") as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {}

        # For each holding/account in the response, store relevant details.
        for holding in investments_data.get("holdings", []):
            account_id = holding.get("account_id")
            existing_data[account_id] = {
                "item_id": item_id,
                "holding": holding,
            }
        save_json_with_backup(LINKED_INVESTMENT_ACCOUNTS, existing_data)
        logger.info(f"Initial investments data saved for item_id {item_id}.")
    except Exception as e:
        logger.error(f"Error in save_initial_investments_data: {e}")


# ------------------------------------------------------------------------------
# Re-use or adjust the exchange_public_token function as needed
# ------------------------------------------------------------------------------


def exchange_public_token(public_token):
    """
    Exchange a public token for an access token.
    This function is shared between products; if your investments flow is different,
    create a dedicated version.
    """
    url = f"https://{PLAID_ENV}.plaid.com/item/public_token/exchange"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "public_token": public_token,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            exchange_data = response.json()
            access_token = exchange_data.get("access_token")
            logger.info(f"Access token generated for investments: {access_token}")
            return access_token
        else:
            logger.error(f"Error exchanging token: {response.json()}")
            return None
    except requests.RequestException as re:
        logger.error(f"Request exception during exchange: {re}")
        return None


def get_categories():
    url = f"https://{PLAID_ENV}.plaid.com/categories/get"
    headers = {"Content-Type": "application/json"}
    payload = {"client_id": PLAID_CLIENT_ID, "secret": PLAID_SECRET}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.json()}
