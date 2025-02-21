# File: app/sql/account_logic.py

import json
from datetime import date, datetime

import requests
from app.config import logger
from app.extensions import db
from app.models import Account, AccountDetails, AccountHistory, Transaction


def upsert_accounts(user_id, accounts_data, batch_size=100):
    """
    Inserts or updates account information from the provided accounts_data.
    If the account type is credit, the balance sign is reversed.
    """
    logger.debug(f"Upserting accounts for user {user_id}: {accounts_data}")
    processed_ids = set()
    count = 0

    for account in accounts_data:
        account_id = account.get("id")
        if not account_id:
            logger.warning("Encountered an account with no 'id'; skipping.")
            continue

        if account_id in processed_ids:
            logger.warning(
                f"Duplicate account id {account_id} encountered; skipping duplicate."
            )
            continue
        processed_ids.add(account_id)

        name = account.get("name") or "Unnamed Account"
        acc_type = account.get("type") or "Unknown"
        balance = account.get("balance", {}).get("current", 0) or 0

        # If account type is credit, reverse the balance sign.
        if acc_type.lower() == "credit":
            logger.debug(f"Account {account_id} is credit; reversing balance sign.")
            balance = -abs(balance)

        subtype = account.get("subtype") or "Unknown"
        status = account.get("status") or "Unknown"
        institution = account.get("institution", {}) or {}
        institution_name = institution.get("name") or "Unknown"
        enrollment_id = account.get("enrollment_id") or ""
        refresh_links = account.get("links") or {}
        link_type = "Teller"

        logger.debug(f"Processing account id: {account_id}")
        existing = Account.query.filter_by(account_id=account_id).first()
        now = datetime.utcnow()
        if existing:
            logger.debug(f"Updating account {account_id}")
            existing.name = name
            existing.type = acc_type
            existing.balance = balance
            existing.subtype = subtype
            existing.status = status
            existing.institution_name = institution_name
            existing.last_refreshed = now
            existing.link_type = link_type
            if existing.details:
                existing.details.enrollment_id = enrollment_id
                existing.details.refresh_links = json.dumps(refresh_links)
            else:
                details = AccountDetails(
                    account_id=account_id,
                    enrollment_id=enrollment_id,
                    refresh_links=json.dumps(refresh_links),
                )
                db.session.add(details)
        else:
            logger.debug(f"Inserting new account {account_id}")
            new_account = Account(
                account_id=account_id,
                user_id=user_id,
                name=name,
                type=acc_type,
                balance=balance,
                subtype=subtype,
                status=status,
                institution_name=institution_name,
                last_refreshed=now,
                link_type=link_type,
            )
            db.session.add(new_account)
            db.session.flush()  # Ensure new_account gets an ID before adding details.
            details = AccountDetails(
                account_id=account_id,
                enrollment_id=enrollment_id,
                refresh_links=json.dumps(refresh_links),
            )
            db.session.add(details)

        # Insert a historical record if not already present for today.
        today = date.today()
        existing_history = AccountHistory.query.filter_by(
            account_id=account_id, date=today
        ).first()
        if not existing_history:
            history_record = AccountHistory(
                account_id=account_id, date=today, balance=balance
            )
            db.session.add(history_record)

        count += 1
        if count % batch_size == 0:
            db.session.commit()
            logger.debug(f"Committed batch of {batch_size} accounts.")

    db.session.commit()  # Commit any remaining accounts
    logger.debug("Finished upserting accounts.")


def refresh_account_data_for_account(
    account, access_token, teller_dot_cert, teller_dot_key, teller_api_base_url
):
    """
    Refreshes account balance and transactions by querying the Teller API.
    Updates the account balance and adds/updates transactions accordingly.
    """
    updated = False
    now = datetime.utcnow()

    # --- Refresh Balance ---
    url_balance = f"{teller_api_base_url}/accounts/{account.account_id}/balances"
    logger.debug(
        f"Requesting balance for account {account.account_id} from {url_balance}"
    )
    resp_balance = requests.get(
        url_balance, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )
    if resp_balance.status_code == 200:
        logger.debug(
            f"Balance response for account {account.account_id}: {resp_balance.text}"
        )
        balance_json = resp_balance.json()
        new_balance = account.balance  # default fallback

        # If response contains "available", we decide which key to use based on account type.
        if "available" in balance_json:
            account_type = account.type.lower() if account.type else ""
            # For credit or liability accounts, use the "ledger" value.
            if account_type in ["credit", "liability"]:
                try:
                    new_balance = float(balance_json.get("ledger", account.balance))
                    logger.debug(
                        "Extracted balance using key 'ledger' for credit/liability account."
                    )
                except Exception as e:
                    logger.error(f"Error parsing 'ledger' balance: {e}", exc_info=True)
                    new_balance = account.balance
            else:
                # For depository accounts, use the "available" value.
                try:
                    new_balance = float(balance_json.get("available", account.balance))
                    logger.debug(
                        "Extracted balance using key 'available' for depository account."
                    )
                except Exception as e:
                    logger.error(
                        f"Error parsing 'available' balance: {e}", exc_info=True
                    )
                    new_balance = account.balance
        # Fallback: existing logic for nested "balance" or "balances" keys.
        elif isinstance(balance_json, dict) and "balance" in balance_json:
            new_balance = (
                balance_json.get("balance", {}).get("current", account.balance) or 0
            )
            logger.debug("Extracted balance using nested 'balance' key.")
        elif isinstance(balance_json, dict) and "balances" in balance_json:
            balances_list = balance_json.get("balances", [])
            if balances_list:
                new_balance = balances_list[0].get("current", account.balance) or 0
                logger.debug(
                    "Extracted balance from the first element of 'balances' list."
                )
            else:
                logger.warning(
                    f"'balances' list is empty for account {account.account_id}."
                )
                new_balance = account.balance
        else:
            logger.warning(
                f"Unexpected balance response format for account {account.account_id}: {balance_json}"
            )
            new_balance = account.balance

        if new_balance != account.balance:
            logger.debug(
                f"Account {account.account_id}: Balance updated from {account.balance} to {new_balance}"
            )
            account.balance = new_balance
            updated = True
        else:
            logger.debug(
                f"Account {account.account_id}: Balance remains unchanged: {account.balance}"
            )
    else:
        logger.error(
            f"Failed to refresh balance for account {account.account_id}: {resp_balance.text}"
        )

    # --- Refresh Transactions ---
    url_txns = f"{teller_api_base_url}/accounts/{account.account_id}/transactions"
    logger.debug(
        f"Requesting transactions for account {account.account_id} from {url_txns}"
    )
    resp_txns = requests.get(
        url_txns, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )
    if resp_txns.status_code == 200:
        logger.debug(
            f"Transactions response for account {account.account_id}: {resp_txns.text}"
        )
        txns_json = resp_txns.json()
        if isinstance(txns_json, dict) and "transactions" in txns_json:
            txns_list = txns_json.get("transactions", [])
            logger.debug(
                f"Extracted {len(txns_list)} transactions from key 'transactions'."
            )
        elif isinstance(txns_json, list):
            txns_list = txns_json
            logger.debug(
                f"Response is a list of transactions with {len(txns_list)} items."
            )
        else:
            logger.warning(
                f"Unexpected transactions format for account {account.account_id}: {txns_json}"
            )
            txns_list = []

        for txn in txns_list:
            txn_id = txn.get("id")
            if not txn_id:
                logger.warning(
                    "Encountered a transaction without an 'id'; skipping this transaction."
                )
                continue

            try:
                existing_txn = Transaction.query.filter_by(
                    transaction_id=txn_id
                ).first()
            except Exception as ex:
                logger.error(
                    f"Error querying transaction {txn_id}: {ex}", exc_info=True
                )
                existing_txn = None

            # Process transaction details.
            details = txn.get("details", {}) or {}
            category = details.get("category")
            if isinstance(category, list) and category:
                category = category[-1] or "Unknown"
            else:
                category = category or "Unknown"

            counterparty = details.get("counterparty")
            merchant_name = "Unknown"
            merchant_typ = "Unknown"
            if isinstance(counterparty, list):
                if counterparty and isinstance(counterparty[0], dict):
                    merchant_name = counterparty[0].get("name", "Unknown")
                    merchant_typ = counterparty[0].get("type", "Unknown")
                    logger.debug(
                        f"Extracted merchant details from list for transaction {txn_id}."
                    )
                else:
                    logger.debug(
                        f"Counterparty list for transaction {txn_id} is empty or improperly formatted."
                    )
            elif isinstance(counterparty, dict):
                merchant_name = counterparty.get("name", "Unknown")
                merchant_typ = counterparty.get("type", "Unknown")
                logger.debug(
                    f"Extracted merchant details from dict for transaction {txn_id}."
                )
            else:
                logger.debug(
                    f"Counterparty for transaction {txn_id} is of unexpected type: {type(counterparty)}"
                )

            if existing_txn:
                logger.debug(
                    f"Updating existing transaction {txn_id} for account {account.account_id}."
                )
                existing_txn.amount = txn.get("amount") or 0
                existing_txn.date = txn.get("date") or ""
                existing_txn.description = txn.get("description") or ""
                existing_txn.category = category
                existing_txn.merchant_name = merchant_name
                existing_txn.merchant_typ = merchant_typ
            else:
                logger.debug(
                    f"Inserting new transaction {txn_id} for account {account.account_id}."
                )
                new_txn = Transaction(
                    transaction_id=txn_id,
                    account_id=account.account_id,
                    amount=txn.get("amount") or 0,
                    date=txn.get("date") or "",
                    description=txn.get("description") or "",
                    category=category,
                    merchant_name=merchant_name,
                    merchant_typ=merchant_typ,
                )
                db.session.add(new_txn)
        updated = True
    else:
        logger.error(
            f"Failed to refresh transactions for account {account.account_id}: {resp_txns.text}"
        )

    # --- Update Last Refreshed and Account History ---
    account.last_refreshed = now
    today = date.today()
    existing_history = AccountHistory.query.filter_by(
        account_id=account.account_id, date=today
    ).first()
    if not existing_history:
        logger.debug(
            f"Creating new history record for account {account.account_id} for date {today}."
        )
        history_record = AccountHistory(
            account_id=account.account_id, date=today, balance=account.balance
        )
        db.session.add(history_record)
        updated = True
    else:
        logger.debug(
            f"History record already exists for account {account.account_id} for date {today}."
        )

    return updated


def get_accounts_from_db():
    """
    Fetch all saved accounts from the database and return as a list of dictionaries.
    """
    accounts = Account.query.all()
    serialized = []
    for acc in accounts:
        serialized.append(
            {
                "account_id": acc.account_id,
                "user_id": acc.user_id,
                "name": acc.name or "Unnamed Account",
                "type": acc.type or "Unknown",
                "subtype": acc.subtype or "Unknown",
                "status": acc.status or "Unknown",
                "institution_name": acc.institution_name or "Unknown",
                "balance": acc.balance if acc.balance is not None else 0,
                "last_refreshed": acc.last_refreshed.isoformat()
                if acc.last_refreshed
                else None,
                "link_type": acc.link_type or "Unknown",
            }
        )
    return serialized


def get_paginated_transactions(page, page_size):
    """
    Returns a tuple (transactions_list, total_count) where each transaction record
    includes fields from both the Transaction and the associated Account.
    """
    query = (
        db.session.query(Transaction, Account)
        .join(Account, Transaction.account_id == Account.account_id)
        .order_by(Transaction.date.desc())
    )
    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    serialized = []
    for txn, acc in results:
        serialized.append(
            {
                "transaction_id": txn.transaction_id,
                "date": txn.date or "",
                "amount": txn.amount if txn.amount is not None else 0,
                "description": txn.description or "",
                "category": txn.category or "Unknown",
                "merchant_name": txn.merchant_name or "Unknown",
                # Account fields:
                "account_name": acc.name or "Unnamed Account",
                "institution_name": acc.institution_name or "Unknown",
                "subtype": acc.subtype or "Unknown",
            }
        )
    return serialized, total
