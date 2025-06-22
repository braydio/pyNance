# File: app/helpers/teller_helpers.py

import json
import requests

from app.config import FILES, TELLER_API_BASE_URL, logger
from app.sql.forecast_logic import update_account_history

TELLER_CERTIFICATE = FILES["TELLER_DOT_CERT"]
TELLER_PRIVATE_KEY = FILES["TELLER_DOT_KEY"]
TELLER_TOKENS = FILES["TELLER_TOKENS"]


def get_teller_accounts(access_token: str, user_id: str):
    """
    Fetch accounts from Teller API for a given access_token and user_id.
    Updates local account history after fetching balances.
    """
    url = f"{TELLER_API_BASE_URL}/accounts"
    response = requests.get(
        url,
        auth=(access_token, ""),
        cert=(TELLER_CERTIFICATE, TELLER_PRIVATE_KEY),
    )
    response.raise_for_status()
    accounts = response.json()

    # Update AccountHistory with latest balances
    for acct in accounts:
        account_id = acct.get("id")
        balance = acct.get("available_balance") or acct.get("current_balance")
        if account_id and balance is not None:
            update_account_history(
                account_id=account_id, user_id=user_id, balance=balance
            )

    return accounts


def load_tokens():
    """
    Load Teller tokens from the designated JSON file.
    Returns list of tokens or an empty list if not found/error.
    """
    try:
        logger.debug(f"Loading tokens from {TELLER_TOKENS}")
        with open(TELLER_TOKENS, "r") as f:
            tokens = json.load(f)
        logger.debug(f"Loaded tokens: {tokens}")
        return tokens
    except FileNotFoundError:
        logger.warning(
            f"Tokens file not found at {TELLER_TOKENS}, returning empty list."
        )
        return []
    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding tokens file at {TELLER_TOKENS}: {e}",
            exc_info=True,
        )
        return []


def save_tokens(tokens):
    """
    Save Teller tokens to the designated JSON file.
    """
    try:
        logger.debug(f"Saving tokens to {TELLER_TOKENS}: {tokens}")
        with open(TELLER_TOKENS, "w") as f:
            json.dump(tokens, f, indent=4)
        logger.debug("Tokens saved successfully.")
    except Exception as e:
        logger.error(f"Error saving tokens to {TELLER_TOKENS}: {e}", exc_info=True)
