# account_logic.py
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
from app.helpers.plaid_helpers import (
    get_transactions,
    get_accounts,
    resolve_or_create_category,
)

from sqlalchemy.orm import aliased
from sqlalchemy.dialects.sqlite import insert

ParentCategory = aliased(Category)

TRANSACTIONS_RAW = FILES["LAST_TX_REFRESH"]
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
    logger.debug(f"[CHECK] upsert_accounts received user_id={user_id}")

    for account in account_list:
        try:
            account_id = account.get("account_id") or account.get("id")
            if not account_id or account_id in processed_ids:
                logger.warning(
                    f"Skipping invalid or duplicate account id: {account_id}"
                )
                continue
            processed_ids.add(account_id)

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

            # Patched: safely upsert AccountHistory with conflict resolution
            today = datetime.utcnow().date()
            stmt = (
                insert(AccountHistory)
                .values(
                    account_id=account_id,
                    user_id=user_id,
                    date=today,
                    balance=balance,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                .on_conflict_do_update(
                    index_elements=["account_id", "date"],
                    set_={
                        "balance": balance,
                        "updated_at": datetime.utcnow(),
                    },
                )
            )
            db.session.execute(
                stmt
            )  # <-- PATCHED: conflict-safe upsert via insert().on_conflict_do_update

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
    from datetime import datetime, date as pydate
    import json
    from tempfile import NamedTemporaryFile

    updated = False
    account_id = account.account_id
    user_id = account.user_id
    balance = account.balance

    # Refresh Balance
    url_balance = f"{teller_api_base_url}/accounts/{account_id}/balances"
    resp_balance = fetch_url_with_backoff(
        url_balance, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )

    if resp_balance.status_code == 200:
        logger.debug(f"Balance response for account {account_id}: {resp_balance.text}")
        balance_json = resp_balance.json()
        new_balance = balance

        if "available" in balance_json:
            account_type = (account.type or "").lower()
            try:
                if account_type in ["credit", "liability"]:
                    new_balance = -float(balance_json.get("ledger", balance))
                    logger.debug(f"Inverting ledger balance for {account_id}")
                else:
                    new_balance = float(balance_json.get("available", balance))
                    logger.debug(f"Using available balance for {account_id}")
            except Exception as e:
                logger.error(f"Error parsing balance: {e}", exc_info=True)

        elif isinstance(balance_json, dict):
            if "balance" in balance_json:
                new_balance = balance_json.get("balance", {}).get("current", balance)
                logger.debug("Extracted balance from 'balance.current'")
            elif "balances" in balance_json and balance_json["balances"]:
                new_balance = balance_json["balances"][0].get("current", balance)
                logger.debug("Extracted balance from 'balances' list")
            else:
                logger.warning(f"No balance data for {account_id}")

        if new_balance != balance:
            account.balance = new_balance
            balance = new_balance
            updated = True
            logger.debug(f"Updated balance for {account_id}: {new_balance}")
        else:
            logger.debug(f"No change to balance for {account_id}")
    else:
        logger.error(f"Failed to refresh balance for {account_id}: {resp_balance.text}")

    # Refresh Transactions
    url_txns = f"{teller_api_base_url}/accounts/{account_id}/transactions"
    logger.debug(f"Requesting transactions for {account_id} from {url_txns}")
    resp_txns = fetch_url_with_backoff(
        url_txns, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )

    if resp_txns.status_code == 200:
        txns_json = resp_txns.json()
        try:
            with NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
                json.dump(txns_json, f, indent=4)
        except Exception as e:
            logger.warning(f"Could not dump raw transactions: {e}")

        txns_list = (
            txns_json.get("transactions", [])
            if isinstance(txns_json, dict)
            else txns_json
            if isinstance(txns_json, list)
            else []
        )

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

            new_amount = process_transaction_amount(
                txn.get("amount") or 0, account.type
            )
            raw_date_str = txn.get("date") or ""
            try:
                parsed_date = datetime.strptime(raw_date_str, "%Y-%m-%d").date()
            except ValueError:
                parsed_date = pydate.today()

            category_list = txn.get("category", [])
            category = (
                " > ".join(category_list)
                if isinstance(category_list, list)
                else "Unknown"
            )

            counterparty = txn.get("details", {}).get("counterparty", {})
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
                    logger.debug(f"Preserving user-modified txn {txn_id}")
                else:
                    logger.debug(f"Updating transaction {txn_id}")
                    existing_txn.amount = new_amount
                    existing_txn.date = parsed_date
                    existing_txn.description = txn.get("description") or ""
                    existing_txn.category = category
                    existing_txn.merchant_name = merchant_name
                    existing_txn.merchant_type = merchant_type
            else:
                logger.debug(f"Inserting new transaction {txn_id}")
                new_txn = Transaction(
                    transaction_id=txn_id,
                    account_id=account_id,
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
            f"Failed to refresh transactions for {account_id}: {resp_txns.text}"
        )

    # Finalize AccountHistory
    today = datetime.utcnow().date()
    existing_history = AccountHistory.query.filter_by(
        account_id=account_id, date=today
    ).first()
    if existing_history:
        logger.debug(
            f"[UPDATING] AccountHistory for account_id={account_id} on {today}"
        )
        existing_history.balance = balance
        existing_history.updated_at = datetime.utcnow()
    else:
        logger.debug(
            f"[CREATING] AccountHistory for account_id={account_id} on {today}"
        )
        new_history = AccountHistory(
            account_id=account_id,
            user_id=user_id,
            date=today,
            balance=balance,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(new_history)

    return updated


def get_paginated_transactions(page, page_size):
    query = (
        db.session.query(Transaction, Account)
        .join(Account, Transaction.account_id == Account.account_id)
        .order_by(Transaction.date.desc())
    )

    total = query.count()

    results = query.offset((page - 1) * page_size).limit(page_size).all()

    serialized = []
    for tx, acc in results:
        serialized.append(
            {
                "transaction_id": tx.transaction_id,
                "date": tx.date.isoformat() if tx.date else None,
                "amount": tx.amount or 0,
                "description": tx.description or tx.merchant_name or "N/A",
                "category": (
                    tx.category.display_name
                    if hasattr(tx.category, "display_name")
                    else tx.category or "Uncategorized"
                ),
                "merchant_name": tx.merchant_name or "Unknown",
                "account_name": acc.name or "Unnamed Account",
                "institution_name": acc.institution_name or "Unknown",
                "subtype": acc.subtype or "Unknown",
                "account_id": acc.account_id or "Unknown",
                "pending": getattr(tx, "pending", False),
                "isEditing": False,
            }
        )

    return serialized, total


def refresh_data_for_plaid_account(access_token, account_id):
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
        account = Account.query.filter_by(account_id=account_id).first()

        if not account:
            logger.warning(f"[DB Lookup] No account found for account_id={account_id}")
            return False

        account_label = account.name or f"[unnamed account] {account_id}"

        transactions = get_transactions(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(f"Fetched {len(transactions)} transactions from Plaid.")

        for txn in transactions:
            txn_id = txn.get("transaction_id")
            if not txn_id:
                logger.warning(
                    f"Transaction missing 'transaction_id'; skipping. Account: {account_label}"
                )
                continue

            txn_date = txn.get("date")
            if isinstance(txn_date, str):
                try:
                    txn_date = datetime.strptime(txn_date, "%Y-%m-%d").date()
                except ValueError:
                    logger.warning(f"Invalid date format for txn {txn_id}; skipping.")
                    continue

            category_path = txn.get("category", [])
            plaid_cat_id = txn.get("category_id")

            category_path = txn.get("category", [])
            primary = category_path[0] if len(category_path) > 0 else "Unknown"
            detailed = category_path[1] if len(category_path) > 1 else "Unknown"

            existing_category = (
                db.session.query(Category)
                .filter_by(primary_category=primary, detailed_category=detailed)
                .first()
            )

            if existing_category:
                category = existing_category
            else:
                category = Category(
                    primary_category=primary,
                    detailed_category=detailed,
                    display_name=f"{primary} > {detailed}",
                )
                db.session.add(category)
                db.session.flush()

            existing_category = (
                db.session.query(Category)
                .filter_by(primary_category=primary, detailed_category=detailed)
                .first()
            )

            if existing_category:
                category = existing_category
            else:
                category = Category(
                    primary_category=primary,
                    detailed_category=detailed,
                    display_name=f"{primary} > {detailed}",
                )
                db.session.add(category)
                db.session.flush()

            merchant_name = txn.get("merchant_name") or "Unknown"
            merchant_type = (
                txn.get("payment_meta", {}).get("payment_method") or "Unknown"
            )
            description = txn.get("name") or "[no description]"
            pending = txn.get("pending", False)

            existing_txn = Transaction.query.filter_by(transaction_id=txn_id).first()

            if existing_txn:
                needs_update = (
                    existing_txn.amount != txn.get("amount")
                    or existing_txn.date != txn_date
                    or existing_txn.description != description
                    or existing_txn.pending != pending
                    or existing_txn.category_id != category.id
                    or existing_txn.merchant_name != merchant_name
                    or existing_txn.merchant_type != merchant_type
                )
                if needs_update:
                    existing_txn.amount = txn.get("amount")
                    existing_txn.date = txn_date
                    existing_txn.description = description
                    existing_txn.pending = pending
                    existing_txn.category_id = category.id
                    existing_txn.category = category.computed_display_name
                    existing_txn.merchant_name = merchant_name
                    existing_txn.merchant_type = merchant_type
                    existing_txn.provider = "Plaid"
                    logger.info(
                        f"Updated transaction {txn_id} for account {account_label}"
                    )
                    updated = True
            else:
                new_txn = Transaction(
                    transaction_id=txn_id,
                    amount=txn.get("amount"),
                    date=txn_date,
                    description=description,
                    pending=pending,
                    account_id=account_id,
                    category_id=category.id,
                    category=category.computed_display_name,
                    merchant_name=merchant_name,
                    merchant_type=merchant_type,
                    provider="Plaid",
                )
                db.session.add(new_txn)
                logger.info(
                    f"➕ Inserted new transaction {txn_id} for account {account_label}"
                )
                updated = True

        db.session.commit()

    except Exception as e:
        logger.error(
            f"Error refreshing transactions for account {account_id}: {e}",
            exc_info=True,
        )
        db.session.rollback()
