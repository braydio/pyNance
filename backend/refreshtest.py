#!/usr/bin/env python3
import json
from app import create_app
from app.extensions import db
from app.models import Account
from app.sql import account_logic
from app.config import FILES, TELLER_API_BASE_URL, logger

# Get the certificate and key paths from our config
TELLER_DOT_CERT = FILES["TELLER_DOT_CERT"]
TELLER_DOT_KEY = FILES["TELLER_DOT_KEY"]
RAW_FILE = FILES["TRANSACTIONS_RAW"]


def refresh_all_accounts():
    accounts = Account.query.all()
    updated_accounts = []
    # Load tokens from the Teller tokens file
    try:
        with open(FILES["TELLER_TOKENS"], "r") as f:
            tokens = json.load(f)
    except Exception as e:
        logger.error(f"Error loading tokens: {e}")
        return updated_accounts

    for account in accounts:
        access_token = None
        for token in tokens:
            if token.get("user_id") == account.user_id:
                access_token = token.get("access_token")
                break
        if not access_token:
            logger.error(f"No access token found for account {account.account_id}")
            continue

        # Call our refresh function (which uses documented Teller endpoints)
        updated = account_logic.refresh_account_data_for_account(
            account, access_token, TELLER_DOT_CERT, TELLER_DOT_KEY, TELLER_API_BASE_URL
        )
        if updated:
            updated_accounts.append(account.account_id)
    db.session.commit()
    return updated_accounts


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        updated = refresh_all_accounts()
        print(f"Refresh completed. Updated accounts: {updated}")
