import os
from pathlib import Path

# Define the base directory for your project
base_dir = Path("myapp")
app_dir = base_dir / "app"

# Create directory structure
directories = [
    base_dir,
    app_dir,
    base_dir / "templates",
    base_dir / "static",
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)

# 1. Create myapp/app/__init__.py
init_py = r"""from flask import Flask
from config import setup_logger
from sql_utils import init_db
from app.routes import main as main_blueprint
from app.settings import settings as settings_blueprint
from app.debug import debug as debug_blueprint

logger = setup_logger()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # Initialize the SQL database.
    init_db()
    
    # Register blueprints.
    app.register_blueprint(main_blueprint)
    app.register_blueprint(settings_blueprint)
    app.register_blueprint(debug_blueprint)
    
    return app
"""
with open(app_dir / "__init__.py", "w", encoding="utf-8") as f:
    f.write(init_py)

# 2. Create myapp/app/plaid_api.py
plaid_api_py = r"""import json
import os
from datetime import datetime
from pathlib import Path
import requests
from config import PLAID_BASE_URL, PLAID_CLIENT_ID, PLAID_ENV, PLAID_SECRET, FILES, DIRECTORIES, setup_logger
from helper_utils import ensure_directory_exists, ensure_file_exists, load_json, save_json_with_backup
from sql_utils import save_accounts_to_db, save_initial_db, save_account_balances

logger = setup_logger()
LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
TEMP_DIR = DIRECTORIES["TEMP_DIR"]

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

        return {"message": "Access token processed successfully.", "item_id": item_id, "institution_name": institution_name}, 200

    except Exception as e:
        logger.error(f"Error processing access token: {e}")
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
    logger.info(f"POST {url} with payload: see debug log.")
    logger.debug(f"Payload: {json.dumps(masked_payload, indent=2)}")
    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            exchange_data = save_and_parse_response(response, os.path.join(TEMP_DIR, "exchange_response.json"))
            access_token = exchange_data.get("access_token")
            logger.info(f"Access token generated: {access_token}")
            return access_token
        else:
            logger.error(f"Error exchanging token: {response.json()}")
            return None
    except requests.RequestException as re:
        logger.error(f"Request exception during exchange: {re}")
        return None

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
        institution_name = item_data["item"].get("institution_name", "Unknown Institution")
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
                "institution_name": account_data["item"].get("institution_name", "Unknown Institution"),
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
"""
with open(app_dir / "plaid_api.py", "w", encoding="utf-8") as f:
    f.write(plaid_api_py)

# 3. Create myapp/app/transactions.py
transactions_py = r"""import json
from datetime import datetime
from config import FILES, setup_logger
from helper_utils import load_transactions_json, load_json, save_json_with_backup, validate_transaction, enrich_transaction
from sql_utils import save_transactions_to_db

logger = setup_logger()
TRANSACTIONS_LIVE = FILES["TRANSACTIONS_LIVE"]
TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]

def process_transactions():
    try:
        transactions = load_transactions_json(TRANSACTIONS_RAW)
        logger.debug(f"Loaded {len(transactions)} raw transactions.")
        accounts = load_json(FILES["LINKED_ACCOUNTS"])
        items = load_json(FILES["LINKED_ITEMS"])
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
        existing_data = load_transactions_json(TRANSACTIONS_LIVE)
        logger.debug(f"Loaded {len(existing_data)} existing transactions.")
        unique_transactions = {tx["transaction_id"]: tx for tx in (existing_data + enriched_transactions)}
        final_transactions = list(unique_transactions.values())
        logger.info("Saving final transactions to SQL database...")
        save_transactions_to_db(final_transactions, accounts)
        save_json_with_backup(TRANSACTIONS_LIVE, {"transactions": final_transactions})
        logger.info(f"Updated TRANSACTIONS_LIVE with {len(final_transactions)} transactions.")
        return {"status": "success", "message": "Transactions processed successfully."}
    except Exception as e:
        logger.error(f"Error in process_transactions: {e}")
        return {"status": "error", "message": str(e)}
"""
with open(app_dir / "transactions.py", "w", encoding="utf-8") as f:
    f.write(transactions_py)

# 4. Create myapp/app/routes.py
routes_py = r"""from flask import Blueprint, render_template, jsonify, request
import json, os
from datetime import datetime, timedelta
from config import FILES, DIRECTORIES, setup_logger
from app.plaid_api import exchange_public_token, get_item_info, save_initial_account_data, refresh_plaid_item
from app.transactions import process_transactions

logger = setup_logger()
main = Blueprint('main', __name__)

LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
TRANSACTIONS_LIVE = FILES["TRANSACTIONS_LIVE"]
TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]

@main.route("/")
def dashboard():
    logger.debug("Rendering dashboard.html")
    return render_template("dashboard.html")

@main.route("/refresh_item", methods=["POST"])
def refresh_item():
    data = request.json
    item_id = data.get("item_id")
    product = data.get("product")
    if not item_id or not product:
        return jsonify({"error": "Missing item_id or product type"}), 400
    try:
        with open(LINKED_ITEMS, "r") as f:
            linked_items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Could not load linked items"}), 500
    item_data = linked_items.get(item_id)
    if not item_data:
        return jsonify({"error": f"Item ID {item_id} not found"}), 404
    access_token = item_data.get("access_token")
    if not access_token:
        return jsonify({"error": f"Access token not found for item {item_id}"}), 400
    if product not in item_data.get("products", []):
        return jsonify({"error": f"Product {product} not linked to item {item_id}"}), 400
    response_data = refresh_plaid_item(access_token, product)
    if not response_data:
        return jsonify({"error": f"Failed to refresh {product} for item {item_id}"}), 500
    item_status = item_data.get("status", {})
    item_status.setdefault("transactions", {})["last_successful_update"] = datetime.utcnow().isoformat()
    item_data["status"] = item_status
    linked_items[item_id] = item_data
    with open(LINKED_ITEMS, "w") as f:
        json.dump(linked_items, f, indent=4)
    return jsonify({"status": "success", "message": f"{product} refreshed", "data": response_data})

@main.route("/save_public_token", methods=["POST"])
def save_public_token():
    try:
        if not request.is_json:
            logger.error("Invalid request: Content-Type must be application/json")
            return jsonify({"error": "Invalid Content-Type. Must be application/json."}), 400
        data = request.get_json()
        logger.debug(f"Received POST data: {json.dumps(data, indent=2)}")
        public_token = data.get("public_token")
        if public_token:
            temp_dir = DIRECTORIES["TEMP_DIR"]
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            with open(os.path.join(temp_dir, "public_token.txt"), "w") as f:
                f.write(public_token)
            logger.info("Public token saved to file")
            access_token = exchange_public_token(public_token)
            if access_token:
                item_id, institution_name = get_item_info(access_token)
                if item_id:
                    save_initial_account_data(access_token, item_id)
                    logger.info(f"Linked to {institution_name} with item ID: {item_id}")
                    return jsonify({"message": f"Linked to {institution_name} successfully", "access_token": access_token}), 200
                else:
                    logger.error("Failed to retrieve item metadata")
                    return jsonify({"error": "Failed to retrieve item metadata"}), 400
            else:
                logger.error("No public token provided")
                return jsonify({"error": "No public token provided"}), 400
    except Exception as e:
        logger.error(f"Error processing public token: {e}")
        return jsonify({"error": "Server error", "details": str(e)}), 500
"""
with open(app_dir / "routes.py", "w", encoding="utf-8") as f:
    f.write(routes_py)

# 5. Create myapp/app/settings.py
settings_py = r"""from flask import Blueprint, render_template, jsonify, request
from helper_utils import get_available_themes, get_current_theme, set_theme
settings = Blueprint('settings', __name__)

@settings.route("/settings")
def settings_page():
    return render_template("settings.html")

@settings.route("/themes", methods=["GET"])
def fetch_themes():
    try:
        themes = get_available_themes()
        current_theme = get_current_theme()
        return jsonify({"themes": themes, "current_theme": current_theme}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@settings.route("/set_theme", methods=["POST"])
def change_theme():
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
"""
with open(app_dir / "settings.py", "w", encoding="utf-8") as f:
    f.write(settings_py)

# 6. Create myapp/app/debug.py
debug_py = r"""from flask import Blueprint, jsonify
from pathlib import Path
from config import DIRECTORIES, THEMES_DIR, DATA_DIR, TEMP_DIR

debug = Blueprint('debug', __name__)

@debug.route("/debug")
def debug_info():
    return jsonify({
        "current_working_directory": str(Path.cwd()),
        "themes_directory": str(THEMES_DIR.resolve()),
        "data_directory": str(DATA_DIR.resolve()),
        "temp_directory": str(TEMP_DIR.resolve()),
    })
"""
with open(app_dir / "debug.py", "w", encoding="utf-8") as f:
    f.write(debug_py)

# 7. Create myapp/run.py
run_py = r"""from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
"""
with open(base_dir / "run.py", "w", encoding="utf-8") as f:
    f.write(run_py)

print("Project structure created in the 'myapp' directory.")
