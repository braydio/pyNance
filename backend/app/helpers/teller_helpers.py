# File: app/helpers/teller_helpers.py

import json
import requests
from app.sql.forecast_logic import update_account_history
from app.config import FILES, TELLER_API_BASE_URL, logger



def get_teller_accounts(access_token: str, user_id: str):
    url = f"{TELLER_API_BASE_URL}/accounts"
    response = requests.get(
        url,
        auth=(access_token, ""),
        cert=(FILES["TELLER_DOT_CERT"], FILES["TELLER_DOT_KEY"]),
    )
    response.raise_for_status()
    accounts = response.json()

    # Update AccountHistory
    for acct in accounts:
        account_id = acct.get("id")
        balance = acct.get("available_balance") or acct.get("current_balance")
        if account_id and balance is not None:
            update_account_history(account_id=account_id, user_id=user_id, balance=balance)

    return accounts


def load_tokens():
    """
    Load Teller tokens from the designated JSON file.
    """
    try:
        logger.debug(f"Loading tokens from {FILES['TELLER_TOKENS']}")
        with open(FILES["TELLER_TOKENS"], "r") as f:
            tokens = json.load(f)
            logger.debug(f"Loaded tokens: {tokens}")
            return tokens
    except FileNotFoundError:
        logger.warning(
            f"Tokens file not found at {FILES['TELLER_TOKENS']}, returning empty list."
        )
        return []
    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding tokens file at {FILES['TELLER_TOKENS']}: {e}",
            exc_info=True,
        )
        return []


def save_tokens(tokens):
    """
    Save Teller tokens to the designated JSON file.
    """
    try:
        logger.debug(f"Saving tokens to {FILES['TELLER_TOKENS']}: {tokens}")
        with open(FILES["TELLER_TOKENS"], "w") as f:
            json.dump(tokens, f, indent=4)
        logger.debug("Tokens saved successfully.")
    except Exception as e:
        logger.error(
            f"Error saving tokens to {FILES['TELLER_TOKENS']}: {e}", exc_info=True
        )
