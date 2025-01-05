import os
import json
import logging
from flask import Flask, jsonify, send_from_directory, request
from create_token import generate_link_token
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV")

# Set up logging
logging.basicConfig(filename='plaid_api.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Route to generate and return a link token
@app.route('/get_link_token', methods=['GET'])
def get_link_token():
    products_param = request.args.get("products")
    if products_param:
        products = products_param.split(",")
    else:
        products = ["transactions", "investments", "liabilities"]

    logging.debug(f"Generating link token for products: {products}")
    link_token = generate_link_token(products)
    if link_token:
        return jsonify({"link_token": link_token})
    else:
        return jsonify({"error": "Failed to create link token"}), 400

# Route to serve the link.html file
@app.route('/')
def serve_link_html():
    return send_from_directory('.', 'link.html')

# Route to save the public token and exchange it for an access token
@app.route('/save_public_token', methods=['POST'])
def save_public_token():
    data = request.json
    logging.debug(f"Received POST data: {json.dumps(data, indent=2)}")
    
    public_token = data.get("public_token")
    if public_token:
        with open("public_token.txt", "w") as f:
            f.write(public_token)

        # Exchange the public token for an access token
        access_token = exchange_public_token(public_token)
        if access_token:
            # Get item metadata
            item_id, institution_name = get_item_info(access_token)
            if item_id:
                # Get and save initial account data
                save_initial_account_data(access_token, item_id)
                return jsonify({"message": f"Linked to {institution_name} successfully", "access_token": access_token}), 200
            else:
                return jsonify({"error": "Failed to retrieve item metadata"}), 400
        else:
            return jsonify({"error": "Failed to exchange public token for access token"}), 400
    else:
        return jsonify({"error": "No public token provided"}), 400

def exchange_public_token(public_token):
    """ Function to exchange public token for access token """
    url = f"https://{PLAID_ENV}.plaid.com/item/public_token/exchange"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "client_id": CLIENT_ID,
        "secret": SECRET_KEY,
        "public_token": public_token
    }
    logging.debug(f"POST {url} with payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload, headers=headers)
    logging.debug(f"Response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        logging.info(f"Access token generated: {access_token}")
        return access_token
    else:
        logging.error(f"Error exchanging token: {response.json()}")
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
    logging.debug(f"POST {url} with payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload, headers=headers)
    logging.debug(f"Response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        item_data = response.json()
        institution_name = item_data.get("institution_name", "Unknown Institution")
        item_id = item_data.get("item", {}).get("item_id")
        logging.info(f"Linked institution: {institution_name} (Item ID: {item_id})")
        return item_id, institution_name
    else:
        logging.error(f"Error fetching item data: {response.json()}")
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
    logging.debug(f"POST {url} with payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload, headers=headers)
    logging.debug(f"Response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        account_data = response.json()
        if os.path.exists("account_data.json"):
            with open("account_data.json", "r") as f:
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

        with open("account_data.json", "w") as f:
            json.dump(data, f, indent=2)

        logging.info(f"Account data saved successfully for item_id {item_id}.")
    else:
        logging.error(f"Error fetching account data: {response.json()}")

if __name__ == "__main__":
    app.run(debug=True)

