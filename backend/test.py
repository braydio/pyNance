#!/usr/bin/env python3
"""
A development utility to simulate linking an account.
It accepts token info (access token and user ID),
fetches account data from Teller, and upserts the data into the database.
"""

import json
import sys

import requests
from app import create_app
from app.config import FILES, TELLER_API_BASE_URL, logger
from app.sql import account_logic

# Use the shared certificate paths from config.
TELLER_DOT_CERT = FILES["TELLER_DOT_CERT"]
TELLER_DOT_KEY = FILES["TELLER_DOT_KEY"]


def extract_accounts_from_response(data):
    """
    Given response JSON data, return the list of accounts.
    If data is a dict and contains an "accounts" key, return that.
    Otherwise, assume data is already the list.
    """
    if isinstance(data, dict):
        return data.get("accounts", data)
    return data


def dev_write_token_info(token_info):
    """
    Given token info (a dict with 'access_token' and 'user_id'),
    fetch accounts from Teller and upsert them into the database.

    :param token_info: dict, e.g.
         {
            "access_token": "token_example",
            "user_id": "user_example"
         }
    """
    access_token = token_info.get("access_token")
    user_id = token_info.get("user_id")
    if not access_token or not user_id:
        logger.error("Token info must include both 'access_token' and 'user_id'.")
        return

    url_accounts = f"{TELLER_API_BASE_URL}/accounts"
    try:
        response = requests.get(
            url_accounts,
            cert=(TELLER_DOT_CERT, TELLER_DOT_KEY),
            auth=(access_token, ""),
        )
    except Exception as e:
        logger.error(f"Error calling Teller API: {e}")
        return

    if response.status_code != 200:
        logger.error(f"Failed to fetch accounts: {response.text}")
        return

    try:
        data = response.json()
        accounts_data = extract_accounts_from_response(data)
    except Exception as e:
        logger.error(f"Error parsing response JSON: {e}")
        return

    try:
        account_logic.upsert_accounts(user_id, accounts_data)
        logger.info("Accounts upserted successfully.")
    except Exception as e:
        logger.error(f"Error writing accounts to database: {e}")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # You can pass token info from the command line as JSON
        if len(sys.argv) > 1:
            try:
                token_info = json.loads(sys.argv[1])
            except Exception as e:
                logger.error(f"Invalid token info JSON: {e}")
                sys.exit(1)
        else:
            # Example token info – replace with valid values for testing.
            token_info = {"user_id": "", "access_token": ""}
        dev_write_token_info(token_info)
