# File: app/sql/account_logic.py

import json
import time
from datetime import date as pydate
from datetime import datetime, timedelta

import requests
from app.config import FILES, PLAID_CLIENT_ID, PLAID_SECRET, logger
from app.extensions import db
from app.models import (
    Account,
    AccountDetails,
    AccountHistory,
    Category,
    PlaidItem,
    Transaction,
)

TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]
TRANSACTIONS_RAW_ENRICHED = FILES["TRANSACTIONS_RAW_ENRICHED"]


def process_transaction_amount(amount, account_type):
    """
    Process the transaction amount based on the account type.

    For credit accounts (i.e. types "credit", "credit card", "credit_card", "liability"),
    assume that positive amounts (charges) should be stored as negative expenses.
    For non-credit accounts, return the amount as-is.
    """
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        return 0.0
    if account_type and account_type.strip().lower() in [
        "credit",
        "credit card",
        "credit_card",
        "liability",
    ]:
        # If a charge comes in as positive, record it as negative.
        if amt > 0:
            return -abs(amt)
        else:
            return amt
    else:
        return amt


def save_plaid_item(user_id, item_id, access_token, institution_name, product):
    """
    Save or update a PlaidItem record in the database.
    """
    item = PlaidItem.query.filter_by(item_id=item_id).first()
    if item:
        item.access_token = access_token
        item.institution_name = institution_name
        item.updated_at = datetime.utcnow()
    else:
        item = PlaidItem(
            user_id=user_id,
            item_id=item_id,
            access_token=access_token,
            institution_name=institution_name,
            product=product,
        )
        db.session.add(item)
    db.session.commit()
    return item


def upsert_accounts(user_id, accounts_data, provider="Unknown", batch_size=100):
    """
    Inserts or updates account information from the provided accounts_data.
    For liability accounts like credit cards, the balance sign is reversed.
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
        normalized_type = acc_type.strip().lower()
        balance = account.get("balance", {}).get("current", 0) or 0

        # For credit/liability accounts, invert the sign on the balance.
        if normalized_type in ["credit", "credit card", "credit_card", "liability"]:
            logger.debug(
                f"Account {account_id} is {normalized_type}; inverting balance from {balance} to {-balance}."
            )
            balance = -balance

        subtype = (account.get("subtype") or "Unknown").capitalize()
        status = account.get("status") or "Unknown"
        institution = account.get("institution", {}) or {}
        institution_name = institution.get("name") or "Unknown"
        enrollment_id = account.get("enrollment_id") or ""
        refresh_links = account.get("links") or {}
        access_token = account.get("access_token") or ""

        logger.debug(f"Processing account id: {account_id}")
        existing = Account.query.filter_by(account_id=account_id).first()
        now = datetime.utcnow()

        # If the account already exists, update it. Otherwise, insert new.
        if existing:
            logger.debug(f"Updating account {name}, {account_id}")
            existing.name = name
            existing.access_token = access_token
            existing.type = acc_type
            existing.balance = balance
            existing.subtype = subtype
            existing.status = status
            existing.institution_name = institution_name
            existing.last_refreshed = now
            existing.link_type = provider
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
                access_token=access_token,
                name=name,
                type=acc_type,
                balance=balance,
                subtype=subtype,
                status=status,
                institution_name=institution_name,
                last_refreshed=now,
                link_type=provider,
            )
            db.session.add(new_account)
            db.session.flush()  # Ensure new_account has an ID before details.
            details = AccountDetails(
                account_id=account_id,
                enrollment_id=enrollment_id,
                refresh_links=json.dumps(refresh_links),
            )
            db.session.add(details)

        # Update daily balance history
        today = pydate.today()
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

    db.session.commit()
    logger.debug("Finished upserting accounts.")


def refresh_plaid_categories(plaid_base_url):
    """
    Call Plaid's categories endpoint and populate the Categories table.
    If a category already exists, it will be skipped.
    """
    url_categories = f"{plaid_base_url}/categories/get"
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
    }
    try:
        resp = requests.post(url_categories, json=payload, timeout=10)
        logger.debug(
            f"Plaid categories endpoint response: {resp.status_code} - {resp.text}"
        )
        if resp.status_code == 200:
            data = resp.json()
            categories = data.get("categories", [])
            for cat in categories:
                plaid_cat_id = cat.get("category_id")
                # Plaid returns a hierarchy list (e.g., ["Travel", "Taxi"])
                hierarchy = cat.get("hierarchy", [])
                primary_category = hierarchy[0] if hierarchy else "Unknown"
                detailed_category = hierarchy[-1] if hierarchy else "Unknown"
                display_name = " > ".join(hierarchy) if hierarchy else "Unknown"
                # Check if this category is already in the DB.
                existing_cat = Category.query.filter_by(
                    plaid_category_id=plaid_cat_id
                ).first()
                if not existing_cat:
                    new_cat = Category(
                        plaid_category_id=plaid_cat_id,
                        primary_category=primary_category,
                        detailed_category=detailed_category,
                        display_name=display_name,
                    )
                    db.session.add(new_cat)
                    logger.debug(f"Inserted new category: {new_cat}")
            db.session.commit()
            logger.debug("Plaid categories refreshed successfully.")
        else:
            logger.error(f"Failed to refresh categories from Plaid: {resp.text}")
    except Exception as e:
        logger.error(f"Exception while refreshing categories: {e}", exc_info=True)


def fetch_url_with_backoff(url, cert, auth, max_retries=3, initial_delay=10):
    """
    Perform a GET request with exponential backoff if a 429 (rate-limit) response is received.
    """
    wait_time = initial_delay
    for attempt in range(1, max_retries + 1):
        resp = requests.get(url, cert=cert, auth=auth)
        if resp.status_code != 429:
            return resp
        logger.warning(
            f"Received 429 on attempt {attempt} for {url}. Sleeping {wait_time} seconds."
        )
        time.sleep(wait_time)
        wait_time *= 2
    return resp


def refresh_data_for_teller_account(
    account, access_token, teller_dot_cert, teller_dot_key, teller_api_base_url
):
    """
    Refresh Teller-linked account by querying the Teller API to update balance and transactions.
    Preserves user-modified transactions by skipping updates on transactions flagged as modified by the user.
    """
    updated = False
    # Refresh Balance
    url_balance = f"{teller_api_base_url}/accounts/{account.account_id}/balances"
    resp_balance = fetch_url_with_backoff(
        url_balance, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )
    if resp_balance.status_code == 200:
        logger.debug(
            f"Balance response for account {account.account_id}: {resp_balance.text}"
        )
        balance_json = resp_balance.json()
        new_balance = account.balance

        # If "available" is present, use that for non-credit accounts; for credit,
        # invert the ledger balance. Otherwise, handle nested structures.
        if "available" in balance_json:
            account_type = (account.type or "").lower()
            if account_type in ["credit", "liability"]:
                try:
                    ledger_value = float(balance_json.get("ledger", account.balance))
                    new_balance = -ledger_value
                    logger.debug(
                        f"Inverting ledger balance for account {account.account_id}: {ledger_value} -> {new_balance}"
                    )
                except Exception as e:
                    logger.error(f"Error parsing ledger balance: {e}", exc_info=True)
            else:
                try:
                    new_balance = float(balance_json.get("available", account.balance))
                    logger.debug(
                        f"Using available balance for account {account.account_id}: {new_balance}"
                    )
                except Exception as e:
                    logger.error(f"Error parsing available balance: {e}", exc_info=True)
        elif isinstance(balance_json, dict):
            if "balance" in balance_json:
                new_balance = (
                    balance_json.get("balance", {}).get("current", account.balance) or 0
                )
                logger.debug("Extracted balance using nested 'balance' key.")
            elif "balances" in balance_json:
                balances_list = balance_json.get("balances", [])
                if balances_list:
                    new_balance = balances_list[0].get("current", account.balance) or 0
                    logger.debug("Extracted balance from 'balances' list.")
                else:
                    logger.warning(
                        f"'balances' list empty for account {account.account_id}."
                    )
        else:
            logger.warning(
                f"Unexpected balance format for account {account.account_id}: {balance_json}"
            )

        if new_balance != account.balance:
            logger.debug(
                f"Account {account.account_id}: Balance updated from {account.balance} to {new_balance}"
            )
            account.balance = new_balance
            updated = True
        else:
            logger.debug(f"Account {account.account_id}: Balance unchanged.")
    else:
        logger.error(
            f"Failed to refresh balance for account {account.account_id}: {resp_balance.text}"
        )

    # Refresh Transactions
    url_txns = f"{teller_api_base_url}/accounts/{account.account_id}/transactions"
    logger.debug(
        f"Requesting transactions for account {account.account_id} from {url_txns}"
    )
    resp_txns = fetch_url_with_backoff(
        url_txns, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )
    if resp_txns.status_code == 200:
        logger.debug(
            f"Transactions response for account {account.account_id}: {resp_txns.text}"
        )
        txns_json = resp_txns.json()
        with open(TRANSACTIONS_RAW, "w") as f:
            json.dump(txns_json, f, indent=4)

        if isinstance(txns_json, dict) and "transactions" in txns_json:
            txns_list = txns_json.get("transactions", [])
        elif isinstance(txns_json, list):
            txns_list = txns_json
        else:
            txns_list = []

        for txn in txns_list:
            txn_id = txn.get("id")
            if not txn_id:
                logger.warning("Transaction missing 'id'; skipping.")
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

            # Process common fields
            new_amount = process_transaction_amount(
                txn.get("amount") or 0, account.type
            )
            raw_date_str = txn.get("date") or ""  # e.g. '2025-03-17'
            if raw_date_str:
                try:
                    parsed_date = datetime.strptime(raw_date_str, "%Y-%m-%d").date()
                except ValueError:
                    parsed_date = pydate.today()
            else:
                parsed_date = pydate.today()

            details = txn.get("details", {}) or {}
            category = details.get("category")
            if isinstance(category, list) and category:
                category = category[-1] or "Unknown"
            else:
                category = category or "Unknown"

            counterparty = details.get("counterparty")
            merchant_name = "Unknown"
            merchant_typ = "Unknown"
            if (
                isinstance(counterparty, list)
                and counterparty
                and isinstance(counterparty[0], dict)
            ):
                merchant_name = counterparty[0].get("name", "Unknown")
                merchant_typ = counterparty[0].get("type", "Unknown")
            elif isinstance(counterparty, dict):
                merchant_name = counterparty.get("name", "Unknown")
                merchant_typ = counterparty.get("type", "Unknown")

            if existing_txn:
                if existing_txn.user_modified:
                    logger.debug(
                        f"Transaction {txn_id} is user modified; preserving user changes."
                    )
                    # Skip updating fields that have been modified by the user.
                else:
                    logger.debug(
                        f"Updating transaction {txn_id} for account {account.account_id}."
                    )
                    existing_txn.amount = new_amount
                    existing_txn.date = parsed_date
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
                    amount=new_amount,
                    date=parsed_date,
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

    # Update daily history for this Teller account
    today = datetime.today().date()
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


def refresh_data_for_plaid_account(account, access_token, plaid_base_url):
    """
    Refresh a Plaid-linked account by querying the Plaid API.
    It refreshes balance and transactions and updates the DB accordingly.
    Returns True if any update occurred.
    """
    updated = False
    now = datetime.utcnow()
    logger.debug(f"Refreshing Plaid account {account.account_id}")

    # --- Refresh Balance (unchanged) ---
    url_balance = f"{plaid_base_url}/accounts/get"
    payload_balance = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    try:
        resp_balance = requests.post(url_balance, json=payload_balance)
        logger.debug(
            f"Plaid balance response for {account.account_id}: {resp_balance.status_code} - {resp_balance.text}"
        )
        if resp_balance.status_code == 200:
            resp_balance.json()
            # (Your code to update balance here; omitted for brevity.)
        else:
            logger.error(
                f"Failed to refresh Plaid balance for {account.account_id}: {resp_balance.text}"
            )
    except Exception as e:
        logger.error(
            f"Exception refreshing Plaid balance for {account.account_id}: {e}",
            exc_info=True,
        )

    # --- Refresh Transactions ---
    url_txns = f"{plaid_base_url}/transactions/get"
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    payload_txns = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
        "start_date": start_date,
        "end_date": end_date,
    }
    try:
        resp_txns = requests.post(url_txns, json=payload_txns, timeout=10)
        logger.debug(
            f"Plaid transactions response for {account.account_id}: {resp_txns.status_code} - {resp_txns.text}"
        )
        if resp_txns.status_code == 200:
            txns_json = resp_txns.json()
            transactions = txns_json.get("transactions", [])
            for txn in transactions:
                txn_id = txn.get("transaction_id")
                if not txn_id:
                    logger.warning("Transaction missing 'transaction_id'; skipping.")
                    continue

                existing_txn = Transaction.query.filter_by(
                    transaction_id=txn_id
                ).first()
                # Process common fields.
                amount = (
                    txn.get("amount") or 0
                )  # You can call process_transaction_amount() here if needed.
                date_str = txn.get("date") or txn.get("authorized_date") or ""
                try:
                    parsed_date = (
                        datetime.strptime(date_str, "%Y-%m-%d").date()
                        if date_str
                        else pydate.today()
                    )
                except ValueError:
                    parsed_date = pydate.today()

                # Instead of extracting category as string, use the new relation.
                plaid_cat_id = txn.get("category_id")
                category_obj = None
                if plaid_cat_id:
                    category_obj = Category.query.filter_by(
                        plaid_category_id=plaid_cat_id
                    ).first()

                # Counterparty / Merchant extraction (unchanged).
                merchant_name = txn.get("merchant_name") or txn.get("name") or "Unknown"
                merchant_typ = "Unknown"
                if txn.get("counterparties"):
                    if (
                        isinstance(txn["counterparties"], list)
                        and txn["counterparties"]
                    ):
                        merchant_typ = txn["counterparties"][0].get("type", "Unknown")
                    elif isinstance(txn["counterparties"], dict):
                        merchant_typ = txn["counterparties"].get("type", "Unknown")

                if existing_txn:
                    if existing_txn.user_modified:
                        logger.debug(
                            f"Transaction {txn_id} is user modified; preserving user changes."
                        )
                    else:
                        logger.debug(
                            f"Updating transaction {txn_id} for account {account.account_id}."
                        )
                        existing_txn.amount = amount
                        existing_txn.date = parsed_date
                        existing_txn.description = txn.get("description") or ""
                        existing_txn.merchant_name = merchant_name
                        existing_txn.merchant_typ = merchant_typ
                        existing_txn.category = category_obj
                else:
                    logger.debug(
                        f"Inserting new transaction {txn_id} for account {account.account_id}."
                    )
                    new_txn = Transaction(
                        transaction_id=txn_id,
                        account_id=account.account_id,
                        amount=amount,
                        date=parsed_date,
                        description=txn.get("description") or "",
                        merchant_name=merchant_name,
                        merchant_typ=merchant_typ,
                        category=category_obj,
                    )
                    db.session.add(new_txn)
            updated = True
        else:
            logger.error(
                f"Failed to refresh Plaid transactions for {account.account_id}: {resp_txns.text}"
            )
    except Exception as e:
        logger.error(
            f"Exception refreshing Plaid transactions for {account.account_id}: {e}",
            exc_info=True,
        )

    account.last_refreshed = now
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
                "last_refreshed": acc.last_refreshed or datetime.now(),
                "link_type": acc.link_type or "Unknown",
            }
        )
    return serialized


def get_paginated_transactions(page, page_size):
    """
    Returns a tuple (transactions_list, total_count) with joined Transaction and Account fields.
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
                "date": txn.date or datetime.now(),
                "amount": txn.amount if txn.amount is not None else 0,
                "description": txn.description or "",
                "category": txn.category or "Unknown",
                "merchant_name": txn.merchant_name or "Unknown",
                "account_name": acc.name or "Unnamed Account",
                "institution_name": acc.institution_name or "Unknown",
                "subtype": acc.subtype or "Unknown",
            }
        )
    return serialized, total
