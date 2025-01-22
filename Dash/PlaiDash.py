import os
import json
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")

# Configure Flask
app = Flask(__name__, template_folder="templates", static_folder="static")

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

# Utility Functions
def ensure_directory_exists(directory_path):
    """Ensures a directory exists."""
    os.makedirs(directory_path, exist_ok=True)

def save_json(file_path, data):
    """Save data to a JSON file."""
    ensure_directory_exists(os.path.dirname(file_path))
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_json(file_path):
    """Load data from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

# Routes
@app.route("/")
def dashboard():
    """Render the main dashboard."""
    return render_template("dashboard.html")

@app.route("/get_link_token", methods=["GET"])
def get_link_token():
    """Generate and return a Plaid link token."""
    try:
        # Simulate generating a link token (replace with Plaid API call in production)
        link_token = "mock_link_token_123"
        return jsonify({"link_token": link_token})
    except Exception as e:
        logger.error(f"Error generating link token: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/save_public_token", methods=["POST"])
def save_public_token():
    """Save the public token and exchange it for an access token."""
    try:
        data = request.get_json()
        public_token = data.get("public_token")

        if not public_token:
            return jsonify({"error": "Public token is required."}), 400

        # Simulate exchanging the public token for an access token
        access_token = f"access_token_for_{public_token}"
        save_json("Dash/data/access_tokens.json", {"access_token": access_token})

        return jsonify({"message": "Access token saved!", "access_token": access_token})
    except Exception as e:
        logger.error(f"Error saving public token: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/process_transactions", methods=["POST"])
def process_transactions():
    """Simulate processing transactions."""
    try:
        # Simulated transactions (replace with actual API call)
        transactions = [
            {"date": "2025-01-20", "name": "Amazon", "amount": -120.50},
            {"date": "2025-01-19", "name": "Uber", "amount": -15.75},
            {"date": "2025-01-18", "name": "Salary", "amount": 2500.00},
        ]
        save_json("Dash/data/transactions.json", {"transactions": transactions})
        return jsonify({"status": "success", "message": "Transactions processed!", "data": transactions})
    except Exception as e:
        logger.error(f"Error processing transactions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get_transactions", methods=["GET"])
def get_transactions():
    """Retrieve processed transactions."""
    try:
        transactions = load_json("Dash/data/transactions.json").get("transactions", [])
        return jsonify({"status": "success", "data": transactions})
    except Exception as e:
        logger.error(f"Error retrieving transactions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get_accounts", methods=["GET"])
def get_accounts():
    """Retrieve linked accounts."""
    try:
        # Simulate linked accounts (replace with actual Plaid API call)
        accounts = [
            {"id": "account_1", "name": "Checking Account", "balance": 1000},
            {"id": "account_2", "name": "Savings Account", "balance": 5000},
        ]
        return jsonify({"status": "success", "data": accounts})
    except Exception as e:
        logger.error(f"Error retrieving accounts: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/refresh_transactions/<account_id>", methods=["POST"])
def refresh_transactions(account_id):
    """Refresh transactions for a selected account."""
    try:
        # Simulate refreshing transactions (replace with actual API call)
        transactions = [
            {"date": "2025-01-20", "name": "Amazon", "amount": -120.50, "category": "Shopping"},
            {"date": "2025-01-19", "name": "Uber", "amount": -15.75, "category": "Transportation"},
            {"date": "2025-01-18", "name": "Salary", "amount": 2500.00, "category": "Income"},
        ]
        save_json(f"Dash/data/transactions_{account_id}.json", {"transactions": transactions})
        return jsonify({"status": "success", "data": transactions})
    except Exception as e:
        logger.error(f"Error refreshing transactions for {account_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/themes", methods=["GET", "POST"])
def themes():
    """Get or set the current theme."""
    theme_file = "Dash/data/theme.json"
    if request.method == "GET":
        theme = load_json(theme_file).get("theme", "default")
        return jsonify({"theme": theme})
    elif request.method == "POST":
        data = request.get_json()
        new_theme = data.get("theme", "default")
        save_json(theme_file, {"theme": new_theme})
        return jsonify({"message": "Theme updated!", "theme": new_theme})

@app.route("/spending_by_category", methods=["GET"])
def spending_by_category():
    """Display spending by category."""
    try:
        transactions = load_json("Dash/data/transactions.json").get("transactions", [])
        category_spending = {}
        for transaction in transactions:
            category = transaction.get("category", "Other")
            category_spending[category] = category_spending.get(category, 0) + abs(transaction["amount"])
        return jsonify({"status": "success", "data": category_spending})
    except Exception as e:
        logger.error(f"Error calculating spending by category: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/debug")
def debug():
    """Debugging information."""
    return jsonify({
        "current_working_directory": os.getcwd(),
        "template_folder": app.template_folder,
        "static_folder": app.static_folder,
    })

if __name__ == "__main__":
    logger.info("Starting Flask application")
    app.run(debug=True, port=5003)
