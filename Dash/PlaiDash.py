import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests

from utils.helper_utils import logger, save_json, load_json
from utils.plaid_utils import generate_link_token

from routes import get_available_themes, process_transactions

# Load environment variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")

# Configure Flask
app = Flask(__name__, template_folder="templates", static_folder="static")

logger.debug(f"Initialized log. PlaiDash running, user in {os.getcwd()}")

# Routes
@app.route("/")
def dashboard():
    """Render the main dashboard."""
    return render_template("dashboard.html")

# Link session info
@app.route("/link_session")
def link_status():
    """Check the current status of the link session."""
    try:
        with open("Dash/temp/link_session.json", "r") as f:
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

# Endpoint to set a selected theme
@app.route('/set_theme', methods=['POST'])
def set_theme():
    data = request.json
    selected_theme = data.get('theme', 'default.css')
    if selected_theme not in get_available_themes():
        return jsonify({"error": "Theme not found"}), 404

    # Save the selected theme to a session or cookie (simplified here)
    # This example uses a file to store the theme for simplicity.
    with open('current_theme.txt', 'w') as f:
        f.write(selected_theme)

    return jsonify({"success": True, "theme": selected_theme})

# Get a list of available themes
@app.route("/themes", methods=["GET", "POST"])
def themes():
    """Get or set the current theme."""
    theme_file = "static/themes/current_theme.txt"
    if request.method == "GET":
        theme = load_json(theme_file).get("theme", "default")
        return jsonify({"theme": theme})
    elif request.method == "POST":
        data = request.get_json()
        new_theme = data.get("theme", "default")
        save_json(theme_file, {"theme": new_theme})
        return jsonify({"message": "Theme updated!", "theme": new_theme})

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
