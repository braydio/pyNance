from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import json
import os
import requests
from pathlib import Path
import logging
from datetime import datetime, timedelta

# All paths & files defined in helper_utils.py
from utils.config_utils import *
from utils.plaid_utils import generate_link_token, ensure_directory_exists, ensure_file_exists, refresh_accounts_by_access_token

# Utility to get available themes
def get_available_themes():
    try:
        themes = [f.name for f in THEMES_DIR.glob('*.css')]
        logging.debug(f"Available themes: {themes}")
        return themes
    except Exception as e:
        logging.error(f"Error accessing themes directory: {e}")
        return []

# Other utility functions
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
                logging.info(f"Overwriting stale backup: {backup_path}")
                os.remove(backup_path)
            os.rename(file_path, backup_path)

        # Save the new JSON data to the file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        logging.info(f"Data successfully saved to {file_path}. Backup created at {backup_path}.")

    except OSError as e:
        logging.error(f"File operation failed: {e}")
        raise e

    except json.JSONDecodeError as e:
        logging.error(f"JSON encoding error: {e}")
        raise e

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise e

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
        link_items_file = DATA_DIR / "LinkItems.json"
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
        logger.info(f"Saved item_id {item_id} for institution '{institution_name}' to LinkItems.json.")

        # Return a success response
        return {"message": "Access token processed successfully.", "item_id": item_id, "institution_name": institution_name}, 200

    except Exception as e:
        logger.error(f"Error processing access token: {str(e)}")
        return {"error": str(e)}, 500

def exchange_public_token(public_token):
    url = f"https://{PLAID_ENV}.plaid.com/item/public_token/exchange"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "public_token": public_token
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
            access_token = save_and_parse_response(response, TEMP_DIR / "exchange_response.json").get("access_token")
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
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        item_data = response.json()
        institution_name = item_data["item"].get("institution_name", "Unknown Institution")
        item_id = item_data["item"].get("item_id")

        LINK_ITEMS_FILE = DATA_DIR / "LinkItems.json"
        ensure_file_exists(LINK_ITEMS_FILE, default_content={})

        with open(LINK_ITEMS_FILE, "r") as f:
            existing_data = json.load(f)

        existing_data[item_id] = {
            "institution_name": institution_name,
            "item_id": item_id,
            "products": item_data["item"].get("products", []),
            "status": item_data.get("status", {})
        }

        save_json_with_backup(LINK_ITEMS_FILE, existing_data)

        logger.info(f"Linked to {institution_name} successfully with item ID: {item_id}")
        return item_id, institution_name
    except Exception as e:
        logger.error(f"Error in get_item_info: {e}")
        return None, None

def save_initial_account_data(access_token, item_id):
    url = f"https://{PLAID_ENV}.plaid.com/accounts/get"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        account_data = response.json()

        LINK_ACCOUNT_PATH = DATA_DIR / "LinkAccounts.json"
        ensure_file_exists(LINK_ACCOUNT_PATH, default_content={})

        # Merge new account data
        with open(LINK_ACCOUNT_PATH, "r") as f:
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
                "balances": account.get("balances", {})
            }

        save_json_with_backup(LINK_ACCOUNT_PATH, existing_data)

        logger.info(f"Account data saved successfully for item_id {item_id}.")
    except Exception as e:
        logger.error(f"Error in save_initial_account_data: {e}")

# Configure Flask
app = Flask(__name__, template_folder="templates", static_folder="static")

# Main flask app
@app.route("/")
def dashboard():
    """Render the main dashboard."""
    logging.debug("Rendering dashboard.html")
    return render_template("dashboard.html")

# -- Accounts Link and Refresh and Display -- Accounts Managements
@app.route('/accounts', methods=['GET'])
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
            accounts_data.append({
                "account_id": account_id,
                "account_name": account.get("account_name"),
                "institution_name": account.get("institution_name"),
                "type": account.get("type"),
                "subtype": account.get("subtype"),
                "balances": account.get("balances"),
                "last_successful_update": item_data.get("status", {}).get("transactions", {}).get("last_successful_update"),
                "products": item_data.get("products", []),
            })
        
        return render_template('accounts.html', accounts=accounts_data)
    except Exception as e:
        logger.error(f"Error loading accounts page: {e}")
        return render_template('error.html', error="Failed to load accounts data.")

# Link token routes
@app.route('/save_public_token', methods=['POST'])
def save_public_token():
    try:
        if not request.is_json:
            logger.error("Invalid request: Content-Type must be application/json")
            return jsonify({"error": "Invalid Content-Type. Must be application/json."}), 400

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
                    logger.info(f"Linked to {institution_name} successfully with item ID: {item_id}")
                    return jsonify({"message": f"Linked to {institution_name} successfully", "access_token": access_token}), 200
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
        return jsonify({"error": "Server error while processing public token", "details": str(e)}), 500

@app.route("/link_session")
def link_status():
    """Check the current status of the link session."""
    session_file = TEMP_DIR / "link_session.json"
    try:
        with session_file.open("r") as f:
            session_data = json.load(f)
        logging.debug(f"Link session data: {session_data}")
        return jsonify(session_data), 200
    except FileNotFoundError:
        logging.warning(f"Link session file not found: {session_file}")
        return jsonify({"status": "no_session"}), 404

@app.route('/get_link_token', methods=['GET'])
def get_link_token():
    products_param = request.args.get("products")
    products = products_param.split(",") if products_param else PRODUCTS

    logging.debug(f"Generating link token for products: {products}")
    link_token = generate_link_token(products)
    if link_token:
        logging.info(f"Successfully generated link token with products: {products}")
        return jsonify({"link_token": link_token})
    else:
        logging.error("Failed to create link token")
        return jsonify({"error": "Failed to create link token"}), 400

# Account displays on /accounts route
@app.route('/get_institutions', methods=['GET'])
def get_institutions():
    try:
        # Load LinkItems.json and LinkAccounts.json
        with open('Dash/data/LinkItems.json') as f:
            link_items = json.load(f)
        with open('Dash/data/LinkAccounts.json') as f:
            link_accounts = json.load(f)

        # Aggregate data by institution
        institutions = {}
        for item_id, item_data in link_items.items():
            institution_name = item_data.get('institution_name', 'Unknown Institution')
            if institution_name not in institutions:
                institutions[institution_name] = {
                    'item_id': item_id,
                    'products': item_data.get('products', []),
                    'status': item_data.get('status', {}),
                    'accounts': []
                }

            # Add accounts linked to this item_id
            for account_id, account_data in link_accounts.items():
                if account_data.get('item_id') == item_id:
                    institutions[institution_name]['accounts'].append(account_data)

        return jsonify({"status": "success", "institutions": institutions}), 200
    except Exception as e:
        logging.error(f"Error fetching institutions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_accounts', methods=['GET'])
def get_accounts():
    try:
        with open(LINKED_ACCOUNTS) as f:
            accounts_data = json.load(f)

        accounts = []
        for account_id, account in accounts_data.items():
            accounts.append({
                "id": account_id,
                "name": account.get("account_name", "Unknown Account"),
                "institution": account.get("institution_name", "Unknown Institution"),
                "masked_access_token": "****" + account_id[-4:],  # Example masking
                "balances": {
                    "available": account.get("balances", {}).get("available"),
                    "current": account.get("balances", {}).get("current"),
                },
            })

        return jsonify(accounts), 200
    except Exception as e:
        logger.error(f"Error loading accounts: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/refresh_account', methods=['POST'])
def refresh_data():
    data = request.json
    item_id = data.get("item_id")
    
    if not item_id:
        return jsonify({"error": "Missing item_id"}), 400

    # Load LinkedItems.json
    try:
        with open(LINKED_ITEMS, "r") as f:
            linked_items = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "LinkedItems.json not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error parsing LinkedItems.json"}), 500

    item = linked_items.get(item_id)
    if not item:
        return jsonify({"error": f"Item with ID {item_id} not found"}), 404

    # Determine start_date
    last_successful_update = item.get("status", {}).get("transactions", {}).get("last_successful_update")
    if last_successful_update:
        # Use the last successful update date
        start_date = last_successful_update.split("T")[0]
        logging.debug(f"Using start_date of {start_date}")
    else:
        # Default to 60 days ago
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        logging.debug(f"Using start_date of {start_date}")

    # Use today's date as the end_date
    end_date = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"End date using: {end_date}")

    # Load LinkAccounts.json to fetch the access_token
    try:
        with open(LINKED_ACCOUNTS, "r") as f:
            linked_accounts = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "LinkAccounts.json not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error parsing LinkAccounts.json"}), 500

    access_token = None
    for account_id, account_data in linked_accounts.items():
        if account_data.get("item_id") == item_id:
            access_token = account_data.get("access_token")
            break

    if not access_token:
        return jsonify({"error": f"No access token found for item ID {item_id}"}), 400

    # Payload for the Plaid API request
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
        "start_date": start_date,
        "end_date": end_date
    }

    url = f"{PLAID_BASE_URL}/transactions/get"

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        transactions_data = response.json()
        transactions = transactions_data.get("transactions", [])
        total_transactions = transactions_data.get("total_transactions", 0)

        logging.info(f"Fetched {len(transactions)} transactions (Total: {total_transactions})")

        # Save transactions to a file
        refreshed_data = {
            "item_id": item_id,
            "start_date": start_date,
            "end_date": end_date,
            "transactions": transactions,
            "total_transactions": total_transactions,
        }
        with open("refreshed_transactions.json", "w") as f:
            json.dump(refreshed_data, f, indent=4)

        return jsonify({
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "transactions": transactions,
            "total_transactions": total_transactions
        }), 200

    except requests.exceptions.RequestException as e:
        logging.error(f"Error refreshing account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/refresh_all_accounts', methods=['POST'])
def refresh_all_accounts():
    try:
        data = request.json
        access_token = data.get("access_token")

        if not access_token:
            return jsonify({"status": "error", "error": "Access token is required"}), 400

        # Logic to refresh all accounts linked by this access token
        refreshed_accounts = refresh_accounts_by_access_token(access_token)

        return jsonify({"status": "success", "details": refreshed_accounts}), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/transactions', methods=['GET'])
def transactions_page():
    try:
        # Load transactions, accounts, and items data
        with open('Dash/data/Transactions.json') as tf:
            transactions_data = json.load(tf)
        with open('Dash/data/LinkAccounts.json') as af:
            link_accounts = json.load(af)
        with open('Dash/data/LinkItems.json') as lf:
            link_items = json.load(lf)
        
        # Enrich transactions with account and item details
        enriched_transactions = []
        for transaction in transactions_data.get("transactions", []):
            account_id = transaction["account_id"]
            account_info = link_accounts.get(account_id, {})
            item_info = link_items.get(account_info.get("item_id", ""), {})
            
            enriched_transactions.append({
                "date": transaction["date"],
                "name": transaction["name"],
                "amount": transaction["amount"],
                "category": transaction.get("category", ["Unknown"])[-1],
                "merchant_name": transaction.get("merchant_name", "Unknown"),
                "institution_name": account_info.get("institution_name", "Unknown"),
                "account_name": account_info.get("account_name", "Unknown Account"),
                "account_type": account_info.get("type", "Unknown"),
                "account_subtype": account_info.get("subtype", "Unknown"),
                "last_successful_update": item_info.get("status", {}).get("transactions", {}).get("last_successful_update", "N/A"),
            })
        
        return render_template('transactions.html', transactions=enriched_transactions)
    except Exception as e:
        logging.error(f"Error loading transactions page: {e}")
        return render_template('error.html', error="Failed to load transactions data.")

@app.route('/save_group', methods=['POST'])
def save_group():
    group = request.json
    try:
        # Save group to a file or database
        with open('custom_groups.json', 'a') as f:
            json.dump(group, f)
            f.write('\n')
        return jsonify({"status": "success", "message": "Group saved!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Main Dashboard Visuals
@app.route('/api/cash_flow', methods=['GET'])
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
        ]
    }
    return jsonify(cash_flow_data)


# --- Route for settings.html
@app.route('/settings')
def settings():
    """Render the settings page for selecting themes."""
    return render_template('settings.html')

# Endpoint to fetch themes
@app.route('/themes', methods=['GET'])
def fetch_themes():
    """Fetch available themes and the current theme."""
    themes = get_available_themes()
    current_theme_file = Path('current_theme.txt')
    try:
        current_theme = current_theme_file.read_text().strip()
        logger.debug(f"Current active theme: {DEFAULT_THEME}")
    except FileNotFoundError:
        logger.debug(f"{current_theme_file} not found, defaulting to {DEFAULT_THEME}")
        current_theme = DEFAULT_THEME

    if themes:
        logger.debug(f"Found themes at {current_theme_file}")
        return jsonify({"themes": themes, "current_theme": current_theme}), 200
    else:
        return jsonify({"error": "No themes available", "current_theme": current_theme}), 404

@app.route('/set_theme', methods=['POST'])
def set_theme():
    """Set the selected theme."""
    data = request.json
    selected_theme = data.get('theme')

    if not selected_theme:
        return jsonify({"error": "No theme provided"}), 400

    if selected_theme not in get_available_themes():
        return jsonify({"error": f"Theme '{selected_theme}' not found"}), 404

    current_theme_file = Path('current_theme.txt')
    try:
        current_theme_file.write_text(selected_theme)
        logger.debug(f"Theme updated to: {selected_theme}")
        return jsonify({"success": True, "theme": selected_theme}), 200
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return jsonify({"error": str(e)}), 500

@app.context_processor
def inject_theme():
    try:
        with open('current_theme.txt', 'r') as f:
            current_theme = f.read().strip()
    except FileNotFoundError:
        current_theme = DEFAULT_THEME

    return {"current_theme": current_theme}

# Debugging route
@app.route("/debug")
def debug():
    """Debugging information."""
    return jsonify({
        "current_working_directory": str(Path.cwd()),
        "template_folder": app.template_folder,
        "static_folder": app.static_folder,
        "themes_directory": str(THEMES_DIR.resolve()),
        "data_directory": str(DATA_DIR.resolve()),
        "temp_directory": str(TEMP_DIR.resolve()),
    })

if __name__ == "__main__":
    logging.info("Starting Flask application")
    app.run(host="0.0.0.0", port=5006, debug=True)
