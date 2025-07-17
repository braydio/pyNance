import os

import requests
from flask import Blueprint, Flask, jsonify, request

app = Flask(__name__)

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")  # or "development", "production"
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

plaid_transfers = Blueprint("plaid_transfers", __name__)


@app.route("/pay_credit_card", methods=["POST"])
def pay_credit_card():
    """
    Pull $500 from the user’s linked Checking Account to pay off a credit card bill.
    Expects JSON containing:
      {
        "access_token": "...",   # The user's Plaid access token for the Checking Account
        "account_id": "...",     # The specific Checking Account ID
        "amount": 500.00         # Payment amount
      }
    """
    data = request.json
    access_token = data["access_token"]
    account_id = data["account_id"]
    amount = data["amount"]  # e.g. 500.00

    # Step 1: Create Transfer Authorization
    auth_payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
        "account_id": account_id,
        "type": "debit",  # We are debiting (pulling from) the Checking Account
        "network": "ach",
        "amount": str(amount),  # Must be a string
        "ach_class": "ppd",  # or "ccd"/"web", depends on your use case
        "user": {  # Basic user info for compliance
            "legal_name": "Jane Doe",  # Probably store this from your user records
            "email_address": "jane@example.com",
        },
    }
    auth_url = f"{PLAID_BASE_URL}/transfer/authorization/create"
    auth_response = requests.post(auth_url, json=auth_payload, timeout=30)
    if auth_response.status_code != 200:
        return (
            jsonify({"error": "Authorization failed", "details": auth_response.text}),
            400,
        )

    auth_data = auth_response.json()
    authorization_id = auth_data["authorization"][
        "id"
    ]  # e.g. "transfer-authorization-xyz"

    # Step 2: Create the Transfer
    transfer_payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "authorization_id": authorization_id,
        "idempotency_key": "unique-payment-12345",  # Must be unique for each request
        "type": "debit",
        "network": "ach",
        "amount": str(amount),
        "ach_class": "ppd",
        "user": {"legal_name": "Jane Doe", "email_address": "jane@example.com"},
        "description": "Credit Card Payment",  # Something descriptive
    }
    transfer_url = f"{PLAID_BASE_URL}/transfer/create"
    transfer_resp = requests.post(transfer_url, json=transfer_payload, timeout=30)
    if transfer_resp.status_code != 200:
        return (
            jsonify(
                {"error": "Transfer creation failed", "details": transfer_resp.text}
            ),
            400,
        )

    transfer_data = transfer_resp.json()
    transfer_id = transfer_data["transfer"]["id"]  # e.g. "transfer-abc123"

    # Step 3: (Optional) Mark credit card as paid in your DB or notify the CC servicer.
    # In a real scenario, you might:
    #   - Create an internal transaction record showing the CC got $500
    #   - Or call the credit card company's API to confirm the payment is on the way

    # Step 4: Return the new transfer details to the client
    return (
        jsonify(
            {
                "status": "success",
                "message": f"Initiated credit card payment of ${amount} from checking",
                "transfer_id": transfer_id,
            }
        ),
        200,
    )
