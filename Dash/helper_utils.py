import json
import os
from pathlib import Path

from config import DIRECTORIES, FILES, logger

THEMES_DIR = DIRECTORIES["THEMES_DIR"]
CURRENT_THEME = FILES["CURRENT_THEME"]
DEFAULT_THEME = FILES["DEFAULT_THEME"]


# Misc helper functions
def ensure_directory_exists(directory_path):
    os.makedirs(directory_path, exist_ok=True)


def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            resolved_path = Path(file_path).resolve()
            logger.debug(f"Loaded from {resolved_path}")
            return json.load(f)
    return {}


def save_json_with_backup(file_path, data):
    try:
        backup_path = f"{file_path}.bak"
        if os.path.exists(file_path):
            if os.path.exists(backup_path):
                logger.info(f"Overwriting stale backup: {backup_path}")
                os.remove(backup_path)
            os.rename(file_path, backup_path)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(
            f"Data successfully saved to {file_path}. Backup created at {backup_path}."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise e


def ensure_file_exists(file_path, default_content=None):
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            if default_content is not None:
                if isinstance(default_content, (dict, list)):
                    json.dump(default_content, file, indent=2)
                else:
                    file.write(default_content)
            else:
                file.write("")


# Transactions helper functions
def load_transactions_json(file):
    return load_json(file).get("transactions", [])


def validate_transaction(tx):
    required_keys = ["transaction_id", "date", "amount"]
    return all(key in tx for key in required_keys)


def enrich_transaction(transaction, accounts, items):
    account_info = accounts.get(transaction["account_id"], {})
    item_info = items.get(account_info.get("item_id", ""), {})

    account_type = account_info.get("type", "Unknown")
    amount = transaction["amount"]  # Get transaction amount

    # Adjust amount for credit accounts
    if account_type == "credit" and amount > 0:
        amount = -amount  # Flip positive transactions (expenses) to negative

    return {
        "transaction_id": transaction["transaction_id"],
        "date": transaction["date"],
        "name": transaction["name"],
        "amount": amount,  # Use adjusted amount
        "category": transaction.get("category", ["Unknown"])[
            -1
        ],  # Use the last category in the list
        "merchant_name": transaction.get("merchant_name", "Unknown"),
        "institution_name": account_info.get("institution_name", "Unknown"),
        "account_name": account_info.get("account_name", "Unknown Account"),
        "account_type": account_type,
        "account_subtype": account_info.get("subtype", "Unknown"),
        "last_successful_update": item_info.get("status", {})
        .get("transactions", {})
        .get("last_successful_update", "N/A"),
    }


# Functions for /settings routes and theme handling
def get_available_themes():
    try:
        themes = [f.name for f in THEMES_DIR.glob("*.css")]
        logger.debug(f"Available themes: {themes}")
        return themes
    except Exception as e:
        logger.error(f"Error accessing themes directory: {e}")
        return []


def get_current_theme():
    """Get the currently active theme."""
    try:
        if CURRENT_THEME.exists():
            with open(CURRENT_THEME, "r") as f:
                return f.read().strip()
        logger.info("No current theme file found. Using default theme.")
        return DEFAULT_THEME.name
    except Exception as e:
        logger.error(f"Error reading current theme: {e}")
        return DEFAULT_THEME.name


def set_theme(theme_name):
    """Set the active theme."""
    if theme_name not in get_available_themes():
        raise ValueError(f"Theme '{theme_name}' is not available.")
    try:
        with open(CURRENT_THEME, "w") as f:
            f.write(theme_name)
        logger.info(f"Theme updated to: {theme_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return False
