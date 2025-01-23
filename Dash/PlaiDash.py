from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import json
import os
import requests
from pathlib import Path
import logging

from utils.helper_utils import save_json, load_json, ensure_directory_exists
from utils.plaid_utils import generate_link_token, refresh_plaid_data

logger = logging.getLogger(__name__)

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('Plaid/logs/testing.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")

THEMES_DIR = Path('Dash/static/themes')
DEFAULT_THEME = 'Dash/static/themes/default.css'
DATA_DIR = Path('Dash/data')
TEMP_DIR = Path('Dash/temp')

logger.debug(f"DEFAULT THEME: {DEFAULT_THEME}")
logger.debug(f"THEMES DIR: {THEMES_DIR}")
logger.debug(f"DATA DIR: {DATA_DIR}")
logger.debug(f"TEMP DIR: {TEMP_DIR}")

# Ensure directories exist
for dir_path in [THEMES_DIR, DATA_DIR, TEMP_DIR]:
    if not dir_path.exists():
        logging.warning(f"Directory {dir_path} does not exist. Creating it...")
        dir_path.mkdir(parents=True, exist_ok=True)

# Configure Flask
app = Flask(__name__, template_folder="templates", static_folder="static")

logging.debug(f"Initialized log. PlaiDash running, user in {Path.cwd()}")

# Utility to get available themes
def get_available_themes():
    try:
        themes = [f.name for f in THEMES_DIR.glob('*.css')]
        logging.debug(f"Available themes: {themes}")
        return themes
    except Exception as e:
        logging.error(f"Error accessing themes directory: {e}")
        return []

# Plaid functions

def exchange_public_token(public_token):
    url = f"https://{PLAID_ENV}.plaid.com/item/public_token/exchange"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": CLIENT_ID,
        "secret": SECRET_KEY,
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
            access_token = save_and_parse_response(response, "Plaid/temp/exchange_response.json").get("access_token")
            logger.info(f"Access token generated: {access_token}")
            return access_token
        else:
            logger.error(f"Error exchanging token: {response.json()}")
            return None
    except requests.RequestException as re:
        logger.error(f"Request exception during exchange: {str(re)}")
        return None

def get_item_info(access_token):
    """
    Fetches metadata for the linked item (institution) and parses institution_name.
    """
    url = f"https://{PLAID_ENV}.plaid.com/item/get"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": CLIENT_ID,
        "secret": SECRET_KEY,
        "access_token": access_token
    }

    masked_payload = payload.copy()
    masked_payload["client_id"] = "****"
    masked_payload["secret"] = "****"
    logger.debug(f"POST {url} with payload: {json.dumps(masked_payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            # Save and parse the response
            item_data = save_and_parse_response(response, "./temp/item_get_response.json")

            # Correctly retrieve institution_name directly from the top level of "item"
            institution_name = item_data["item"].get("institution_name", "Unknown Institution")
            item_id = item_data["item"].get("item_id")

            logger.info(f"Extracted institution_name: {institution_name}")

            # Save item metadata to LinkItems.json
            ensure_file_exists("./data/LinkItems.json", default_content={})
            with open("./data/LinkItems.json", "r") as f:
                existing_data = json.load(f)

            existing_data[item_id] = {
                "institution_name": institution_name,
                "item_id": item_id,
                "products": item_data["item"].get("products", []),
                "status": item_data.get("status", {})
            }

            with open("./data/LinkItems.json", "w") as f:
                json.dump(existing_data, f, indent=2)

            logger.info(f"Linked to {institution_name} successfully with item ID: {item_id}")
            return item_id, institution_name
        else:
            logger.error(f"Error fetching item data: {response.json()}")
            return None, None
    except requests.RequestException as re:
        logger.error(f"Request exception during item info retrieval: {str(re)}")
        return None, None
    except KeyError as ke:
        logger.error(f"Key error: {ke}")
        return None, None

def save_initial_account_data(access_token, item_id):
    """
    Fetches and saves account data associated with the given access token and item ID.
    """
    url = f"https://{PLAID_ENV}.plaid.com/accounts/get"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": CLIENT_ID,
        "secret": SECRET_KEY,
        "access_token": access_token
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
            account_data = save_and_parse_response(response, "./temp/accounts_get_response.json")

            # Extract institution_name from item object
            institution_name = account_data["item"].get("institution_name", "Unknown Institution")

            ensure_file_exists("./data/LinkAccounts.json", default_content={})
            with open("./data/LinkAccounts.json", "r") as f:
                data = json.load(f)

            for account in account_data["accounts"]:
                account_id = account["account_id"]
                data[account_id] = {
                    "item_id": item_id,
                    "institution_name": institution_name,
                    "account_name": account["name"],
                    "type": account["type"],
                    "subtype": account["subtype"],
                    "balances": account.get("balances", {})
                }
                logger.info(f"Linked account {account['name']} for institution {institution_name}")

            with open("./data/LinkAccounts.json", "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Account data saved successfully for item_id {item_id}.")
        else:
            logger.error(f"Error fetching account data: {response.json()}")
    except requests.RequestException as re:
        logger.error(f"Request exception during account data retrieval: {str(re)}")
    except KeyError as ke:
        logger.error(f"Key error: {ke}")

# Main flask app
@app.route("/")
def dashboard():
    """Render the main dashboard."""
    logging.debug("Rendering dashboard.html")
    return render_template("dashboard.html")

@app.route('/refresh_data', methods=['POST'])
def refresh_data():
    selected_group = request.json.get('account_group')
    if not selected_group:
        return jsonify({"error": "No account group selected"}), 400
    
    try:
        result = refresh_plaid_data(selected_group)
        return jsonify({"message": "Data refreshed successfully", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            temp_dir = "Plaid/temp"
            ensure_directory_exists(temp_dir)  # Ensure the directory exists

            with open(os.path.join(temp_dir, "public_token.txt"), "w") as f:
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

@app.route("/save_public_token", methods=["POST"])
def save_public_token():
    """Save the public token and exchange it for an access token."""
    try:
        data = request.get_json()
        public_token = data.get("public_token")

        if not public_token:
            return jsonify({"error": "Public token is required."}), 400

        access_token = f"access_token_for_{public_token}"
        access_token_file = DATA_DIR / "access_tokens.json"
        save_json(access_token_file, {"access_token": access_token})

        logging.debug(f"Access token saved to {access_token_file}")
        return jsonify({"message": "Access token saved!", "access_token": access_token})
    except Exception as e:
        logging.error(f"Error saving public token: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_transactions", methods=["GET"])
def get_transactions():
    """Retrieve processed transactions."""
    transactions_file = DATA_DIR / "transactions.json"
    try:
        transactions = load_json(transactions_file).get("transactions", [])
        logging.debug(f"Retrieved transactions from {transactions_file}")
        return jsonify({"status": "success", "data": transactions})
    except Exception as e:
        logging.error(f"Error retrieving transactions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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

# Route for rendering the settings page
@app.route('/settings')
def settings():
    """Render the settings page for selecting themes."""
    return render_template('settings.html')

# Function to get the current theme
@app.context_processor
def inject_theme():
    try:
        with open('current_theme.txt', 'r') as f:
            current_theme = f.read().strip()
    except FileNotFoundError:
        current_theme = DEFAULT_THEME

    return {"current_theme": current_theme}

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
    app.run(debug=True, port=5006)
