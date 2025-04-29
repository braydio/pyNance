# File: app/sql/account_logger.c.py
import json
import time
from datetime import datetime, timedelta, date as pydate
import requests

from app.extensions import db
from app.config import FILES, PLAID_CLIENT_ID, PLAID_SECRET, logger
from app.models import (
    Account,
    AccountHistory,
    Category,
    Transaction,
    PlaidAccount,
    TellerAccount,
)
from app.helpers.plaid_helpers import get_transactions, get_accounts

from sqlalchemy.orm import aliased

ParentCategory = aliased(Category)

TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]
TRANSACTIONS_RAW_ENRICHED = FILES["TRANSACTIONS_RAW_ENRICHED"]


def process_transaction_amount(amount, account_type):
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
        return -abs(amt) if amt > 0 else amt
    return amt


def save_plaid_item(user_id, item_id, access_token, institution_name, product):
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


def upsert_accounts(user_id, account_list, provider):
    processed_ids = set()
    count = 0

    for account in account_list:
        try:
            account_id = account.get("account_id") or account.get("id")
            if not account_id or account_id in processed_ids:
                logger.warning(
                    f"Skipping invalid or duplicate account id: {account_id}"
                )
                continue
            processed_ids.add(account_id)

            allowed_fields = {
                "account_id",
                "user_id",
                "name",
                "type",
                "subtype",
                "institution_name",
                "status",
                "balance",
                "link_type",
            }

            account["user_id"] = user_id

            name = account.get("name") or "Unnamed Account"
            acc_type = str(account.get("type") or "Unknown")
            balance = (
                account.get("balance", {}).get("current", 0)
                or account.get("balance", 0)
                or 0
            )
            balance = process_transaction_amount(balance, acc_type)
            subtype = str(account.get("subtype") or "Unknown").capitalize()
            status = account.get("status") or "Unknown"
            institution_name = (
                (account.get("institution") or {}).get("name")
                or account.get("institution_name")
                or "Unknown"
            )
            refresh_links_json = json.dumps(account.get("links") or {})

            now = datetime.utcnow()
            filtered_account = {
                "account_id": account_id,
                "user_id": user_id,
                "name": name,
                "type": acc_type,
                "subtype": subtype,
                "institution_name": institution_name,
                "status": status,
                "balance": balance,
                "link_type": provider,
            }

            existing_account = Account.query.filter_by(account_id=account_id).first()
            if existing_account:
                logger.debug(f"Updating account {account_id}")
                for key, value in filtered_account.items():
                    setattr(existing_account, key, value)
                existing_account.updated_at = now
            else:
                logger.debug(f"Creating new account {account_id}")
                new_account = Account(**filtered_account)
                db.session.add(new_account)

            # Link Plaid or Teller accounts if applicable
            if provider.lower() == "plaid":
                existing_plaid = PlaidAccount.query.filter_by(
                    account_id=account_id
                ).first()
                if existing_plaid:
                    existing_plaid.access_token = account.get("access_token")
                    existing_plaid.item_id = account.get("item_id")
                    existing_plaid.institution_id = account.get("institution_id")
                    existing_plaid.webhook = account.get("webhook")
                    existing_plaid.last_refreshed = now
                else:
                    new_plaid = PlaidAccount(
                        account_id=account_id,
                        access_token=account.get("access_token"),
                        item_id=account.get("item_id"),
                        institution_id=account.get("institution_id"),
                        webhook=account.get("webhook"),
                        last_refreshed=now,
                    )
                    db.session.add(new_plaid)
            elif provider.lower() == "teller":
                existing_teller = TellerAccount.query.filter_by(
                    account_id=account_id
                ).first()
                if existing_teller:
                    existing_teller.access_token = account.get("access_token")
                    existing_teller.enrollment_id = account.get("enrollment_id")
                    existing_teller.institution_id = account.get("institution_id")
                    existing_teller.last_refreshed = now
                else:
                    new_teller = TellerAccount(
                        account_id=account_id,
                        access_token=account.get("access_token"),
                        enrollment_id=account.get("enrollment_id"),
                        institution_id=account.get("institution_id"),
                        provider="Teller",
                        last_refreshed=now,
                    )
                    db.session.add(new_teller)

            # Update AccountHistory today
            today = pydate.today()
            history = AccountHistory.query.filter_by(
                account_id=account_id, date=today
            ).first()
            if not history:
                db.session.add(
                    AccountHistory(account_id=account_id, date=today, balance=balance)
                )

            count += 1
            if count % 100 == 0:
                db.session.commit()
                logger.debug("Committed batch of 100 accounts.")

        except Exception as e:
            logger.error(f"Failed to upsert account {account_id}: {e}", exc_info=True)

    db.session.commit()
    logger.info("Finished upserting accounts.")


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

            category_list = txn.get("category", [])
            if isinstance(category_list, list) and category_list:
                category = " > ".join(category_list)
            else:
                category = "Unknown"

            counterparty = details.get("counterparty")
            merchant_name = "Unknown"
            merchant_type = "Unknown"
            if (
                isinstance(counterparty, list)
                and counterparty
                and isinstance(counterparty[0], dict)
            ):
                merchant_name = counterparty[0].get("name", "Unknown")
                merchant_type = counterparty[0].get("type", "Unknown")
            elif isinstance(counterparty, dict):
                merchant_name = counterparty.get("name", "Unknown")
                merchant_type = counterparty.get("type", "Unknown")

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
                    existing_txn.merchant_type = merchant_type
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
                    merchant_type=merchant_type,
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
                "transaction_id": txn.transaction_id * -1,
                "date": txn.date or datetime.now(),
                "amount": txn.amount if txn.amount is not None else 0,
                "description": txn.description or "",
                "category": txn.category if txn.category else "Unknown",
                "merchant_name": txn.merchant_name or "Unknown",
                "account_name": acc.name or "Unnamed Account",
                "institution_name": acc.institution_name or "Unknown",
                "subtype": acc.subtype or "Unknown",
                "account_id": acc.account_id or "UnKnown",
            }
        )
    return serialized, total


def refresh_data_for_plaid_account(access_token, account_id, plaid_base_url):
    """
    Refresh all Plaid-linked accounts under a single access_token by querying the Plaid API.
    Refreshes transactions and updates the DB accordingly, ensuring each transaction goes to the correct account.
    Returns True if any update occurred.
    """
    updated = False
    now = datetime.utcnow()

    PLAID_MAX_LOOKBACK_DAYS = 730
    end_date = now.date()
    start_date = (now - timedelta(days=PLAID_MAX_LOOKBACK_DAYS)).date()

    try:
        transactions = get_transactions(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(f"Fetched {len(transactions)} transactions from Plaid.")

        for txn in transactions:
            txn_id = txn.get("transaction_id")
            if not txn_id:
                logger.warning("Transaction missing 'transaction_id'; skipping.")
                continue

            existing_txn = Transaction.query.filter_by(transaction_id=txn_id).first()

            if existing_txn:
                existing_txn.amount = txn.get("amount")
                existing_txn.date = txn.get("date")
                existing_txn.name = txn.get("name")
                logger.info(f"Updated transaction {txn_id}")
            else:
                new_txn = Transaction(
                    transaction_id=txn_id,
                    amount=txn.get("amount"),
                    date=txn.get("date"),
                    name=txn.get("name"),
                    account_id=account_id,  # <-- Now properly defined
                )
                db.session.add(new_txn)
                logger.info(f"Inserted new transaction {txn_id}")

            updated = True

        db.session.commit()

    except Exception as e:
        logger.error(f"Error refreshing transactions: {e}", exc_info=True)
        db.session.rollback()

    return updated
