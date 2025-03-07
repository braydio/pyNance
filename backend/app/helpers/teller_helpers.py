# File: app/helpers/teller_helpers.py

import json

from app.config import FILES, logger


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
