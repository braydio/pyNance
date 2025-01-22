import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from LinkMake import generate_link_token
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV")
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")

# Set up logging to both file and terminal
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('Plaid/logs/plaid_api.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Utility functions
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
    
    # Parse the saved file
    return load_json(file_path)

def load_json(file_path):
    """
    Load JSON content from a file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON content from the file.
    """
    with open(file_path, "r") as temp_file:
        app.run(debug=True, port=5001)

app = Flask(__name__, template_folder='templates')

# Route to serve the link.html file
@app.route('/')
def serve_link_html():
    logger.debug("Serving link.html to user")   
    return render_template('landing.html')

@app.route('/link_status', methods=['GET'])
def link_status():
    """Check the current status of the link session."""
    try:
        with open("Plaid/temp/link_session.json", "r") as f:
            session_data = json.load(f)
        return jsonify(session_data), 200
    except FileNotFoundError:
        return jsonify({"status": "no_session"}), 404

# Route to generate and return a link token
@app.route('/get_link_token', methods=['GET'])
def get_link_token():
    products_param = request.args.get("products")
    if products_param:
        products = products_param.split(",")
    else:
        products = PRODUCTS

    logger.debug(f"Generating link token for products: {products}")
    link_token = generate_link_token(products)
    if link_token:
        logger.info(f"Successfully generated link token with products: {products}")
        return jsonify({"link_token": link_token})
    else:
        logger.error("Failed to create link token")
        return jsonify({"error": "Failed to create link token"}), 400

# Route to save the public token and exchange it for an access token
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

if __name__ == '__main__':
    logger.info("Starting Flask application for Plaid integration")
    print("Current working directory:", os.getcwd())
    print("Template folder:", app.template_folder)
    app.run(debug=True, port=5001)