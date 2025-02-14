import inspect
import json
import os
from pathlib import Path

from app.config import DIRECTORIES, FILES, logger
from app.db_models import SessionLocal
from app.teller_dot_transact import save_transactions_to_db

from flask import jsonify

THEMES_DIR = DIRECTORIES["THEMES_DIR"]
CURRENT_THEME = FILES["CURRENT_THEME"]
DEFAULT_THEME = FILES["DEFAULT_THEME"]


# Misc helper functions
def ensure_directory_exists(directory_path):
    os.makedirs(directory_path, exist_ok=True)


def load_json_safe(file_path):
    """
    Load JSON from the given file. Returns a tuple (data, error) where
    data is the loaded JSON (or {} if errors occur) and error is None or
    a descriptive error message.
    """
    if not os.path.exists(file_path):
        err = f"File not found: {file_path}"
        logger.error(err)
        return {}, err
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Loaded data from {Path(file_path).resolve()}")
        return data, None
    except json.JSONDecodeError as e:
        err = f"JSON decode error in {file_path}: {e}"
        logger.error(err, exc_info=True)
        return {}, err
    except Exception as e:
        err = f"Error reading {file_path}: {e}"
        logger.error(err, exc_info=True)
        return {}, err


def save_json_with_backup(file_path, data):
    """Save JSON data to file, backing up the old file if it exists."""
    try:
        backup_path = f"{file_path}.bak"
        if os.path.exists(file_path):
            if os.path.exists(backup_path):
                logger.info(f"Overwriting stale backup: {backup_path}")
                os.remove(backup_path)
            os.rename(file_path, backup_path)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Data saved to {file_path}; backup at {backup_path}.")
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}", exc_info=True)
        raise e


def ensure_file_exists(file_path, default_content=None):
    """Ensure the file exists. If not, create it with the default content."""
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            if default_content is not None:
                if isinstance(default_content, (dict, list)):
                    json.dump(default_content, file, indent=2)
                else:
                    file.write(default_content)
            else:
                file.write("")


def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            resolved_path = Path(file_path).resolve()
            logger.debug(f"Loaded from {resolved_path}")
            return json.load(f)
    return {}


# Transactions helper functions
def load_transactions_json(file):
    return load_json(file).get("transactions", [])


def validate_transaction(tx):
    required_keys = ["transaction_id", "date", "amount"]
    return all(key in tx for key in required_keys)


def process_transactions(transactions, accounts, items):
    """Processes raw transactions, enriches them, saves them to SQL, and updates live data JSON."""
    try:
        logger.debug("Starting process_transactions")
        logger.debug(f"Processing {len(transactions)} raw transactions.")
        logger.debug(f"Loaded {len(accounts)} accounts, {len(items)} items.")

        enriched_transactions = []
        for tx in transactions:
            if not validate_transaction(tx):
                logger.warning(f"Skipping invalid transaction: {tx}")
                continue
            try:
                enriched_tx = enrich_transaction(tx, accounts, items)
                enriched_transactions.append(enriched_tx)
                logger.debug(f"Enriched transaction: {enriched_tx}")
            except Exception as e:
                logger.error(
                    f"Error enriching transaction: {tx}, error: {e}", exc_info=True
                )

        logger.info(f"Enriched {len(enriched_transactions)} transactions.")

        # Log details about FILES before using it
        logger.debug(f"FILES variable: {FILES} (type: {type(FILES)})")
        try:
            # Log the value for TRANSACTIONS_LIVE
            key_value = (
                FILES.get("TRANSACTIONS_LIVE") if isinstance(FILES, dict) else None
            )
            logger.debug(
                f"FILES['TRANSACTIONS_LIVE']: {key_value} (type: {type(key_value)})"
            )
        except Exception as e:
            logger.error(
                f"Error accessing FILES['TRANSACTIONS_LIVE']: {e}", exc_info=True
            )

        existing_data = load_transactions_json(FILES["TRANSACTIONS_LIVE"])
        logger.debug(
            f"Loaded {len(existing_data)} existing transactions from TRANSACTIONS_LIVE."
        )

        unique_transactions = {
            tx["transaction_id"]: tx for tx in (existing_data + enriched_transactions)
        }
        final_transactions = list(unique_transactions.values())
        logger.debug(
            f"Total unique transactions after deduplication: {len(final_transactions)}"
        )

        logger.info(
            "Saving enriched, deduplicated transactions json & updating SQL database..."
        )

        # Add logging before calling save_transactions_to_db
        logger.debug("Preparing to call save_transactions_to_db.")
        logger.debug(
            f"Final transactions: type: {type(final_transactions)}, length: {len(final_transactions)}"
        )
        logger.debug(
            f"Accounts (linked_accounts): type: {type(accounts)}; content: {accounts}"
        )

        # Log the expected parameters for save_transactions_to_db
        expected_args = inspect.getfullargspec(save_transactions_to_db).args
        logger.debug(
            f"save_transactions_to_db expects the following arguments: {expected_args}"
        )

        # Here, the call is made with only two arguments.
        logger.debug(
            "Calling save_transactions_to_db with two arguments instead of the required three."
        )
        try:
            session = SessionLocal()  # Create a new database session
            # Pass the raw transactions (or you might pass the enriched ones depending on your logic)
            save_transactions_to_db(
                session, final_transactions, FILES["LINKED_ACCOUNTS"]
            )
            session.commit()
            logger.info("Transactions saved to the database.")
        except Exception:
            logger.info("Saved transactions to SQL database.")

        try:
            logger.debug(
                f"About to save JSON backup using key: {FILES['TRANSACTIONS_LIVE']}"
            )
            save_json_with_backup(
                FILES["TRANSACTIONS_LIVE"], {"transactions": final_transactions}
            )
            logger.info(
                f"Updated TRANSACTIONS_LIVE with {len(unique_transactions)} transactions."
            )
        except Exception as e:
            logger.error(f"Error saving JSON backup: {e}", exc_info=True)
            raise

        return (
            jsonify(
                {"status": "success", "message": "Transactions processed successfully."}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error in process_transactions: {e}", exc_info=True)


# Process transactions helper
def enrich_transaction(transaction, accounts, items):
    account_info = accounts.get(transaction["account_id"], {})
    item_info = items.get(account_info.get("item_id", ""), {})

    # Adjust amount for credit accounts
    account_type = account_info.get("type", "Unknown")
    amount = transaction["amount"]  # Get transaction amount
    if account_type == "credit" and amount > 0:
        logger.debug(
            f"Flipped {amount} for expense activity from Account Type: {account_type} on Item ID: {item_info}"
        )
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
