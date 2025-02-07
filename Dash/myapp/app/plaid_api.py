import json
import os
from datetime import datetime
from pathlib import Path

import requests
from config import (
    DIRECTORIES,
    FILES,
    PLAID_CLIENT_ID,
    PLAID_ENV,
    PLAID_SECRET,
    setup_logger,
)
from helper_utils import (
    ensure_directory_exists,
    ensure_file_exists,
    load_json,
    save_json_with_backup,
)
from sql_utils import save_account_balances, save_accounts_to_db, save_initial_db

logger = setup_logger()
LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
TEMP_DIR = DIRECTORIES["TEMP_DIR"]


def process_access_token(public_token):
    try:
        access_token = exchange_public_token(public_token)
        if not access_token:
            return {"error": "Failed to exchange public token for access token."}, 400

        item_id, institution_name = get_item_info(access_token)
        if not item_id:
            return {"error": "Failed to retrieve item metadata."}, 400

        save_initial_account_data(access_token, item_id)

        ensure_file_exists(LINKED_ITEMS, default_content={})
        with open(LINKED_ITEMS, "r") as f:
            existing_items = json.load(f)

        existing_items[item_id] = {
            "institution_name": institution_name,
            "item_id": item_id,
            "access_token": access_token,
            "linked_at": datetime.now().isoformat(),
            "status": {},
        }

        save_json_with_backup(LINKED_ITEMS, existing_items)
        logger.info(f"Saved item_id {item_id} for institution '{institution_name}'.")

        save_initial_db()

        return {
            "message": "Access token processed successfully.",
            "item_id": item_id,
            "institution_name": institution_name,
        }, 200

    except Exception as e:
        logger.error(f"Error processing access token: {e}")
        return {"error": str(e)}, 500


def exchange_public_token(public_token):
    url = f"https://{PLAID_ENV}.plaid.com/item/public_token/exchange"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "public_token": public_token,
    }
    masked_payload = payload.copy()
    masked_payload["client_id"] = "****"
    masked_payload["secret"] = "****"
    logger.info(f"POST {url} with payload: see debug log.")
    logger.debug(f"Payload: {json.dumps(masked_payload, indent=2)}")
    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            exchange_data = save_and_parse_response(
                response, os.path.join(TEMP_DIR, "exchange_response.json")
            )
            access_token = exchange_data.get("access_token")
            logger.info(f"Access token generated: {access_token}")
            return access_token
        else:
            logger.error(f"Error exchanging token: {response.json()}")
            return None
    except requests.RequestException as re:
        logger.error(f"Request exception during exchange: {re}")
        return None


def save_and_parse_response(response, file_path):
    ensure_directory_exists(os.path.dirname(file_path))
    with open(file_path, "w") as temp_file:
        json.dump(response.json(), temp_file, indent=2)
    resolved_path = Path(file_path).resolve()
    logger.debug(f"Saved response to {resolved_path}")
    return load_json(file_path)


def get_item_info(access_token):
    url = f"https://{PLAID_ENV}.plaid.com/item/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        item_data = response.json()
        institution_name = item_data["item"].get(
            "institution_name", "Unknown Institution"
        )
        item_id = item_data["item"].get("item_id")

        ensure_file_exists(LINKED_ITEMS, default_content={})
        with open(LINKED_ITEMS, "r") as f:
            existing_data = json.load(f)

        existing_data[item_id] = {
            "institution_name": institution_name,
            "item_id": item_id,
            "products": item_data["item"].get("products", []),
            "status": item_data.get("status", {}),
        }

        save_json_with_backup(LINKED_ITEMS, existing_data)
        logger.info(f"Linked to {institution_name} with item ID: {item_id}")
        return item_id, institution_name

    except Exception as e:
        logger.error(f"Error in get_item_info: {e}")
        return None, None


def save_initial_account_data(access_token, item_id):
    url = f"https://{PLAID_ENV}.plaid.com/accounts/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        account_data = response.json()
        ensure_file_exists(LINKED_ACCOUNTS, default_content={})
        with open(LINKED_ACCOUNTS, "r") as f:
            existing_data = json.load(f)
        for account in account_data["accounts"]:
            account_id = account["account_id"]
            existing_data[account_id] = {
                "item_id": item_id,
                "institution_name": account_data["item"].get(
                    "institution_name", "Unknown Institution"
                ),
                "access_token": access_token,
                "account_name": account["name"],
                "type": account["type"],
                "subtype": account["subtype"],
                "balances": account.get("balances", {}),
            }
        save_json_with_backup(LINKED_ACCOUNTS, existing_data)
        save_accounts_to_db(account_data["accounts"], item_id)
        save_account_balances(account_data["accounts"])
        logger.info(f"Account data saved for item_id {item_id}.")
    except Exception as e:
        logger.error(f"Error in save_initial_account_data: {e}")
