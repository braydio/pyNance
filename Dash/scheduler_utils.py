import json
import time
from datetime import datetime
from pathlib import Path

import requests
import schedule
from config import PLAID_CLIENT_ID, PLAID_ENV, PLAID_SECRET, setup_logger
from sql_utils import save_account_balances

logger = setup_logger()

LINKED_ACCOUNTS = "LinkAccounts.json"
LINKED_ITEMS = "LinkItems.json"


def fetch_account_info(access_token):
    """Fetch latest account info from Plaid API."""
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
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching account data: {e}")
        return None


def update_account_balances():
    """Periodically update balances for all linked accounts."""
    if not Path(LINKED_ACCOUNTS).exists():
        logger.error(f"Error: {LINKED_ACCOUNTS} not found.")
        return

    with open(LINKED_ACCOUNTS, "r") as f:
        linked_accounts = json.load(f)

    if not Path(LINKED_ITEMS).exists():
        logger.error(f"Error: {LINKED_ITEMS} not found.")
        return

    with open(LINKED_ITEMS, "r") as f:
        json.load(f)

    updated_accounts = []  # Store accounts for DB update

    for account_id, account_data in linked_accounts.items():
        item_id = account_data.get("item_id")

        # Fetch access token from linked accounts, not items
        access_token = account_data.get("access_token")
        if not access_token:
            logger.warning(f"No access token found for item_id {item_id}. Skipping...")
            continue

        new_data = fetch_account_info(access_token)
        if not new_data or "accounts" not in new_data:
            logger.warning(
                f"Failed to fetch account info for item_id {item_id}. Skipping..."
            )
            continue

        for account in new_data["accounts"]:
            if account["account_id"] == account_id:
                linked_accounts[account_id]["balances"] = account.get("balances", {})
                linked_accounts[account_id]["last_updated"] = datetime.now().isoformat()
                updated_accounts.append(account)

    # Save updated balances to file
    with open(LINKED_ACCOUNTS, "w") as f:
        json.dump(linked_accounts, f, indent=4)

    # Save to database
    if updated_accounts:
        save_account_balances(updated_accounts)

    logger.info(f"Updated account balances at {datetime.now().isoformat()}")


# Schedule periodic updates every hour
schedule.every(1).hours.do(update_account_balances)

if __name__ == "__main__":
    logger.info("Starting balance updater...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
