import json

import requests
from config import FILES, TELLER_APP_ID, logger
from flask import Blueprint, jsonify, render_template, request

# Paths for certificates, tokens, and accounts
TELLER_DOT_KEY = FILES["TELLER_DOT_KEY"]
TELLER_DOT_CERT = FILES["TELLER_DOT_CERT"]
TELLER_TOKENS = FILES["TELLER_TOKENS"]
TELLER_ACCOUNTS = FILES["TELLER_ACCOUNTS"]

# Teller API base URL
TELLER_API_BASE_URL = "https://api.teller.io"

# Flask blueprints
link_teller = Blueprint("link_teller", __name__)
main_teller = Blueprint("main_teller", __name__)

"""
This is the process to link a new account to the dashboard using teller.io
It contains routes to 
    - initialize the teller script and start the link process
    - Generate a link token and exchange for the access token
    - Call the teller API with the access token, create a new entry for the account in the SQL DB / live json files
"""


# Utility functions
def load_tokens():
    """Load existing tokens from file."""
    try:
        with open(TELLER_TOKENS, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding tokens: {e}")
        return []


def save_tokens(tokens):
    """Save tokens to file."""
    with open(TELLER_TOKENS, "w") as f:
        json.dump(tokens, f, indent=4)


def initial_get_info(access_token):
    """
    Handles the routing and processing of initial teller link.
    """
    try:
        url = f"{TELLER_API_BASE_URL}/accounts"
        response = requests.get(
            url,
            cert=(TELLER_DOT_CERT, TELLER_DOT_KEY),  # mTLS certificates
            auth=(access_token, ""),  # Basic Auth
        )

        if response.status_code != 200:
            logger.error(
                f"Failed to fetch accounts for token {access_token}: {response.text}"
            )
            return None

        accounts = response.json()

        # Save structured accounts data
        structured_accounts = {
            "accounts": [
                {
                    "id": account["id"],
                    "access_token": access_token,
                    "name": account["name"],
                    "type": account["type"],
                    "subtype": account["subtype"],
                    "last_four": account.get("last_four"),
                    "currency": account["currency"],
                    "status": account["status"],
                    "institution": account["institution"],
                    "links": account["links"],
                    "enrollment_id": account["enrollment_id"],
                }
                for account in accounts
            ]
        }

        with open(TELLER_ACCOUNTS, "w") as f:
            json.dump(structured_accounts, f, indent=4)

        logger.info("Accounts successfully fetched and saved.")
        return structured_accounts

    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        return None


@link_teller.route("/generate_link_token", methods=["POST"])
def generate_link_token():
    """
    Generate a Teller link token to initialize Teller Connect.
    """
    try:
        # Teller API endpoint for creating a link token
        url = f"{TELLER_API_BASE_URL}/link_tokens"
        headers = {
            "Authorization": f"Bearer {TELLER_DOT_KEY}",
            "Content-Type": "application/json",
        }

        # Payload for creating the link token
        payload = {
            "application_id": TELLER_APP_ID,
            "user_id": "Administrator",  # Replace with your logic for user identification
            "products": ["transactions", "balance"],  # Specify the products you need
        }

        # Make the API request to Teller
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error(f"Error generating link token: {response.json()}")
            return (
                jsonify({"status": "error", "message": response.json()}),
                response.status_code,
            )

        # Return the link token to the frontend
        link_token = response.json().get("link_token")
        return jsonify({"status": "success", "link_token": link_token}), 200

    except Exception as e:
        logger.error(f"Unexpected error generating link token: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@main_teller.route("/teller")
def home_teller():
    """Render the teller accounts handler."""
    logger.debug("Rendering teller.html")
    return render_template("teller.html", teller_app_id=TELLER_APP_ID)


@main_teller.route("/exchange_public_token", methods=["POST"])
def exchange_public_token():
    """
    Exchange public_token for access_token via Teller API.
    """
    try:
        data = request.json
        public_token = data.get("public_token")

        if not public_token:
            return jsonify({"error": "Missing public token"}), 400

        url = f"{TELLER_API_BASE_URL}/link_tokens/exchange"
        headers = {"Authorization": f"Bearer {TELLER_DOT_KEY}"}
        payload = {"public_token": public_token}

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            return jsonify({"error": response.json()}), response.status_code

        access_token = response.json().get("access_token")
        user_id = response.json().get("user", {}).get("id")

        tokens = load_tokens()
        tokens.append({"user_id": user_id, "access_token": access_token})
        save_tokens(tokens)

        # Fetch and save accounts immediately
        accounts = initial_get_info(access_token)
        if accounts is None:
            return (
                jsonify({"status": "error", "message": "Failed to fetch accounts"}),
                500,
            )

        return jsonify(
            {"status": "success", "access_token": access_token, "user_id": user_id}
        )

    except Exception as e:
        logger.error(f"Error exchanging public token: {e}")
        return jsonify({"error": str(e)}), 500


@link_teller.route("/save_token", methods=["POST"])
def save_token():
    """
    Save the access token and user ID from Teller Connect, then fetch accounts.
    """
    try:
        data = request.json
        access_token = data.get("access_token")
        user_id = data.get("user_id")

        if not access_token or not user_id:
            return (
                jsonify(
                    {"status": "error", "message": "Missing access token or user ID"}
                ),
                400,
            )

        # Load existing tokens
        tokens = load_tokens()

        # Add the new token
        tokens.append({"user_id": user_id, "access_token": access_token})
        save_tokens(tokens)

        # Fetch and save accounts
        accounts = initial_get_info(access_token)
        if accounts is None:
            return (
                jsonify({"status": "error", "message": "Failed to fetch accounts"}),
                500,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Token and accounts saved successfully",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error saving token: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@link_teller.route("/get_all_accounts", methods=["GET"])
def get_all_accounts():
    """
    Fetch account details for all linked tokens.
    """
    try:
        tokens = load_tokens()
        if not tokens:
            return (
                jsonify({"status": "error", "message": "No access tokens found"}),
                400,
            )

        all_accounts = []

        for token in tokens:
            access_token = token.get("access_token")
            if not access_token:
                continue

            url = f"{TELLER_API_BASE_URL}/accounts"
            response = requests.get(
                url,
                cert=(TELLER_DOT_CERT, TELLER_DOT_KEY),  # mTLS certificates
                auth=(access_token, ""),  # Basic Auth
            )

            if response.status_code == 200:
                accounts = response.json()
                all_accounts.extend(accounts)  # Collect accounts
            else:
                logger.error(f"Failed to fetch accounts for token: {access_token}")

        # Save combined accounts data
        with open(TELLER_ACCOUNTS, "w") as f:
            json.dump(all_accounts, f, indent=4)

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "All accounts fetched successfully",
                    "data": all_accounts,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@link_teller.route("/load_teller_accounts", methods=["GET"])
def load_accounts():
    """
    Serve the saved accounts data from TELLER_ACCOUNTS.
    """
    try:
        with open(TELLER_ACCOUNTS, "r") as f:
            accounts_data = json.load(f)
        return jsonify({"status": "success", "data": accounts_data}), 200
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "No accounts data found"}), 404
    except json.JSONDecodeError as e:
        return jsonify({"status": "error", "message": f"JSON decoding error: {e}"}), 400
    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}),
            500,
        )


@main_teller.route("/logs", methods=["GET"])
def get_logs():
    """
    Fetch the logs of exchanged tokens (for debugging purposes).
    """
    try:
        with open("logs/tokens.json", "r") as f:
            logs = [json.loads(line.strip()) for line in f]
        return jsonify({"logs": logs})
    except FileNotFoundError:
        return jsonify({"logs": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
