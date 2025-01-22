import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from LinkMake import generate_link_token
import requests
from dotenv import load_dotenv

from routes import process_transactions

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

@app.route('/debug_template')
def debug_template():
    template_path = os.path.join(app.template_folder, 'landing.html')
    return jsonify({
        "exists": os.path.exists(template_path),
        "path": template_path
    })


@app.route('/get_linked_accounts', methods=['GET'])
def get_linked_accounts():
    try:
        link_accounts_file = os.path.join(os.path.dirname(__file__), 'Plaid/data/LinkAccounts.json')
        link_items_file = os.path.join(os.path.dirname(__file__), 'Plaid/data/LinkItems.json')
        output_file = os.path.join(os.path.dirname(__file__), 'Dash/data/linked_accounts.json')

        # Load accounts and items
        with open(link_accounts_file, 'r') as laf:
            link_accounts_data = json.load(laf)
        with open(link_items_file, 'r') as lif:
            link_items_data = json.load(lif)

        # Create a list of linked accounts and institutions
        linked_accounts = []
        for account_id, account_data in link_accounts_data.items():
            item_id = account_data.get("item_id", "")
            institution_name = link_items_data.get(item_id, {}).get("institution_name", "Unknown Institution")
            linked_accounts.append({
                "account_id": account_id,
                "account_name": account_data.get("account_name", "Unknown Account"),
                "type": account_data.get("type", "Unknown"),
                "subtype": account_data.get("subtype", "Unknown"),
                "institution_name": institution_name,
                "item_id": item_id
            })

        # Save the linked accounts to a JSON file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(linked_accounts, f, indent=4)

        return jsonify({"status": "success", "data": linked_accounts}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/process_transactions', methods=['POST'])
def process_transactions_route():
    transactions_file = os.path.join(os.path.dirname(__file__), 'Plaid/data/transactions.json')
    link_accounts_file = os.path.join(os.path.dirname(__file__), 'Plaid/data/LinkAccounts.json')
    link_items_file = os.path.join(os.path.dirname(__file__), 'Plaid/data/LinkItems.json')
    output_file = os.path.join(os.path.dirname(__file__), 'Dash/data/processed_transactions.json')
    
    result = process_transactions(transactions_file, link_accounts_file, link_items_file, output_file)
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/get_transactions', methods=['GET'])
def get_processed_transactions():
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'Dash/data/processed_transactions.json')
        with open(file_path, 'r') as f:
            transactions = json.load(f)
        return jsonify({"status": "success", "data": transactions}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Current working directory:", os.getcwd())
    print("Template folder:", app.template_folder)
    app.run(debug=True, port=5002)