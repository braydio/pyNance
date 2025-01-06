import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from create_token import generate_link_token
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

    file_handler = logging.FileHandler('./logs/plaid_api.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

app = Flask(__name__, template_folder='./templates')

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

# Route to serve the link.html file
@app.route('/')
def serve_link_html():
    logger.debug("Serving link.html to user")
    return send_from_directory('.', 'link.html')

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
            with open("./data/public_token.txt", "w") as f:
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
                logger.error("Failed to exchange public token for access token")
                return jsonify({"error": "Failed to exchange public token for access token"}), 400
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
    """ Function to exchange public token for access token """
    url = f"https://{PLAID_ENV}.plaid.com/item/public_token/exchange"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": CLIENT_ID,
        "secret": SECRET_KEY,
        "public_token": public_token
    }
    logger.debug(f"POST {url} with payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            logger.info(f"Access token generated: {access_token}")
            with open("./data/access_token.txt", "w") as f:
                f.write(access_token)
            return access_token
        else:
            logger.error(f"Error exchanging token: {response.json()}")
            return None
    except requests.RequestException as re:
        logger.error(f"Request exception during exchange: {str(re)}")
        return None

def get_item_info(access_token):
    """ Fetches metadata for the linked item (institution) """
    url = f"https://{PLAID_ENV}.plaid.com/item/get"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": CLIENT_ID,
        "secret": SECRET_KEY,
        "access_token": access_token
    }
    logger.debug(f"POST {url} with payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            item_data = response.json()
            institution_name = item_data.get("institution_name", "Unknown Institution")
            item_id = item_data.get("item", {}).get("item_id")
            logger.info(f"Linked institution: {institution_name} (Item ID: {item_id})")
            with open("./data/item_info.json", "w") as f:
                json.dump(item_data, f, indent=2)
            return item_id, institution_name
        else:
            logger.error(f"Error fetching item data: {response.json()}")
            return None, None
    except requests.RequestException as re:
        logger.error(f"Request exception during item info retrieval: {str(re)}")
        return None, None

def save_initial_account_data(access_token, item_id):
    """ Fetches and saves account info after initial link """
    url = f"https://{PLAID_ENV}.plaid.com/accounts/get"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": CLIENT_ID,
        "secret": SECRET_KEY,
        "access_token": access_token
    }
    logger.debug(f"POST {url} with payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            account_data = response.json()
            if os.path.exists("./data/account_data.json"):
                with open("./data/account_data.json", "r") as f:
                    data = json.load(f)
            else:
                data = {}

            for account in account_data["accounts"]:
                account_id = account["account_id"]
                data[account_id] = {
                    "item_id": item_id,
                    "account_name": account["name"],
                    "type": account["type"],
                    "subtype": account["subtype"],
                    "balances": account.get("balances", {})
                }

            if not os.path.exists("./data"):
                os.makedirs("./data")

            with open("./data/account_data.json", "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Account data saved successfully for item_id {item_id}.")
        else:
            logger.error(f"Error fetching account data: {response.json()}")
    except requests.RequestException as re:
        logger.error(f"Request exception during account data retrieval: {str(re)}")

if __name__ == "__main__":
    logger.info("Starting Flask application for Plaid integration")
    app.run(debug=True)

