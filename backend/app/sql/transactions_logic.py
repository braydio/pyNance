"""Transaction refresh and pagination helpers.

This module centralizes logic for retrieving and updating transaction
records from third-party providers. Functions here are shared by route
modules and ``account_logic`` for legacy compatibility.
"""

from __future__ import annotations

import json
import time
from datetime import date as pydate
from datetime import datetime, timedelta, timezone
from tempfile import NamedTemporaryFile

import requests
from app.config import logger
from app.extensions import db
from app.helpers.normalize import normalize_amount
from app.helpers.plaid_helpers import get_accounts, get_transactions
from app.models import Account, AccountHistory, Category, Transaction


def process_transaction_amount(amount):
    """Parse the transaction amount without adjusting signage."""
    return normalize_amount(amount)


def normalize_balance(amount, account_type):
    """Normalize account balance sign based on account type."""
    return normalize_amount(
        {
            "amount": amount,
            "transaction_type": (
                account_type.lower().replace("_", " ") if account_type else None
            ),
        }
    )


def fetch_url_with_backoff(url, cert, auth, max_retries: int = 3, initial_delay: int = 10):
    """Perform a GET request with exponential backoff on HTTP 429."""
    wait_time = initial_delay
    for attempt in range(1, max_retries + 1):
        resp = requests.get(url, cert=cert, auth=auth)
        if resp.status_code != 429:
            return resp
        logger.warning(
            "Received 429 on attempt %s for %s. Sleeping %s seconds.", attempt, url, wait_time
        )
        time.sleep(wait_time)
        wait_time *= 2
    return resp


def refresh_data_for_teller_account(
    account: Account,
    access_token: str,
    teller_dot_cert: str,
    teller_dot_key: str,
    teller_api_base_url: str,
    start_date: str | datetime.date | None = None,
    end_date: str | datetime.date | None = None,
) -> bool:
    """Refresh a Teller account within an optional date range."""

    updated = False
    account_id = account.account_id
    user_id = account.user_id
    balance = account.balance

    end_date_obj = end_date
    start_date_obj = start_date
    if isinstance(end_date_obj, str):
        end_date_obj = datetime.strptime(end_date_obj, "%Y-%m-%d").date()
    if isinstance(start_date_obj, str):
        start_date_obj = datetime.strptime(start_date_obj, "%Y-%m-%d").date()

    # Refresh Balance
    url_balance = f"{teller_api_base_url}/accounts/{account_id}/balances"
    resp_balance = fetch_url_with_backoff(
        url_balance, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )

    if resp_balance.status_code == 200:
        logger.debug("Balance response for account %s: %s", account_id, resp_balance.text)
        balance_json = resp_balance.json()
        new_balance = balance

        if "available" in balance_json:
            account_type = (account.type or "").lower()
            try:
                if account_type in ["credit", "liability"]:
                    new_balance = -float(balance_json.get("ledger", balance))
                    logger.debug("Inverting ledger balance for %s", account_id)
                else:
                    new_balance = float(balance_json.get("available", balance))
                    logger.debug("Using available balance for %s", account_id)
            except Exception as exc:  # noqa: BLE001
                logger.error("Error parsing balance: %s", exc, exc_info=True)
        elif isinstance(balance_json, dict):
            if "balance" in balance_json:
                new_balance = balance_json.get("balance", {}).get("current", balance)
                logger.debug("Extracted balance from 'balance.current'")
            elif "balances" in balance_json and balance_json["balances"]:
                new_balance = balance_json["balances"][0].get("current", balance)
                logger.debug("Extracted balance from 'balances' list")
            else:
                logger.warning("No balance data for %s", account_id)

        if new_balance != balance:
            account.balance = new_balance
            balance = new_balance
            updated = True
            logger.debug("Updated balance for %s: %s", account_id, new_balance)
        else:
            logger.debug("No change to balance for %s", account_id)
    else:
        logger.error("Failed to refresh balance for %s: %s", account_id, resp_balance.text)

    # Refresh Transactions
    url_txns = f"{teller_api_base_url}/accounts/{account_id}/transactions"
    logger.debug("Requesting transactions for %s from %s", account_id, url_txns)
    resp_txns = fetch_url_with_backoff(
        url_txns, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )

    if resp_txns.status_code == 200:
        txns_json = resp_txns.json()
        try:
            with NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
                json.dump(txns_json, f, indent=4)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not dump raw transactions: %s", exc)

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
                existing_txn = Transaction.query.filter_by(transaction_id=txn_id).first()
            except Exception as ex:  # noqa: BLE001
                logger.error("Error querying transaction %s: %s", txn_id, ex, exc_info=True)
                existing_txn = None

            new_amount = process_transaction_amount(txn.get("amount") or 0)
            raw_date_str = txn.get("date") or ""
            try:
                parsed_date = datetime.strptime(raw_date_str, "%Y-%m-%d").date()
            except ValueError:
                parsed_date = pydate.today()

            if start_date_obj and parsed_date < start_date_obj:
                continue
            if end_date_obj and parsed_date > end_date_obj:
                continue

            category_list = txn.get("category", [])
            category = (
                " > ".join(category_list) if isinstance(category_list, list) else "Unknown"
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
                    logger.debug("Preserving user-modified txn %s", txn_id)
                else:
                    logger.debug("Updating transaction %s", txn_id)
                    existing_txn.amount = new_amount
                    existing_txn.date = parsed_date
                    existing_txn.description = txn.get("description") or ""
                    existing_txn.category = category
                    existing_txn.merchant_name = merchant_name
                    existing_txn.merchant_type = merchant_type
            else:
                logger.debug("Inserting new transaction %s", txn_id)
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
            "Failed to refresh transactions for %s: %s", account_id, resp_txns.text
        )

    # Finalize AccountHistory
    today = datetime.now(timezone.utc).date()
    existing_history = AccountHistory.query.filter_by(
        account_id=account_id, date=today
    ).first()
    if existing_history:
        logger.debug("[UPDATING] AccountHistory for account_id=%s on %s", account_id, today)
        existing_history.balance = balance
        existing_history.is_hidden = account.is_hidden
        existing_history.updated_at = datetime.now(timezone.utc)
    else:
        logger.debug("[CREATING] AccountHistory for account_id=%s on %s", account_id, today)
        new_history = AccountHistory(
            account_id=account_id,
            user_id=user_id,
            date=today,
            balance=balance,
            is_hidden=account.is_hidden,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.session.add(new_history)

    return updated


def get_paginated_transactions(
    page: int,
    page_size: int,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    category: str | None = None,
    user_id: str | None = None,
) -> tuple[list[dict], int]:
    """Return serialized transactions for the requested page."""

    query = (
        db.session.query(Transaction, Account)
        .join(Account, Transaction.account_id == Account.account_id)
        .filter(Account.is_hidden.is_(False))
        .order_by(Transaction.date.desc())
    )

    if user_id:
        query = query.filter(Account.user_id == user_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if category:
        query = query.filter(Transaction.category == category)

    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()

    serialized = []
    for txn, acc in results:
        serialized.append(
            {
                "transaction_id": txn.transaction_id,
                "date": txn.date.isoformat() if txn.date else None,
                "amount": txn.amount,
                "description": txn.description or txn.merchant_name or "N/A",
                "category": txn.category or "Uncategorized",
                "merchant_name": txn.merchant_name or "Unknown",
                "account_name": acc.name or "Unnamed Account",
                "institution_name": acc.institution_name or "Unknown",
                "subtype": acc.subtype or "Unknown",
                "account_id": acc.account_id or "Unknown",
                "pending": getattr(txn, "pending", False),
                "isEditing": False,
            }
        )

    return serialized, total


def refresh_data_for_plaid_account(
    access_token: str,
    account_id: str,
    start_date: str | datetime.date | None = None,
    end_date: str | datetime.date | None = None,
) -> bool:
    """Refresh a single Plaid account within an optional date range."""

    updated = False
    now = datetime.now(timezone.utc)

    PLAID_MAX_LOOKBACK_DAYS = 680
    end_date_obj = end_date or now.date()
    start_date_obj = start_date or (now - timedelta(days=PLAID_MAX_LOOKBACK_DAYS)).date()

    if isinstance(end_date_obj, str):
        end_date_obj = datetime.strptime(end_date_obj, "%Y-%m-%d").date()
    if isinstance(start_date_obj, str):
        start_date_obj = datetime.strptime(start_date_obj, "%Y-%m-%d").date()

    try:
        account = Account.query.filter_by(account_id=account_id).first()
        if not account:
            logger.warning("[DB Lookup] No account found for account_id=%s", account_id)
            return False

        accounts_data = get_accounts(access_token, account.user_id)
        for acct in accounts_data:
            if acct.get("account_id") == account_id:
                raw_balance = (
                    acct.get("balances", {}).get("current")
                    or acct.get("balance", {}).get("current")
                    or acct.get("balance")
                    or 0
                )
                account.balance = normalize_balance(raw_balance, account.type)
                account.updated_at = datetime.now(timezone.utc)
                logger.debug(
                    "[REFRESH] Updated balance for %s: %s",
                    account_id,
                    account.balance,
                )
                break

        account_label = account.name or f"[unnamed account] {account_id}"

        transactions = get_transactions(
            access_token=access_token,
            start_date=start_date_obj,
            end_date=end_date_obj,
        )
        logger.info("Fetched %s transactions from Plaid.", len(transactions))
        transactions = [txn for txn in transactions if txn.get("account_id") == account_id]
        logger.info(
            "Processing %s transactions for account %s.", len(transactions), account_id
        )

        for txn in transactions:
            txn_id = txn.get("transaction_id")
            if not txn_id:
                logger.warning(
                    "Transaction missing 'transaction_id'; skipping. Account: %s",
                    account_label,
                )
                continue

            txn_date = txn.get("date")
            if isinstance(txn_date, str):
                try:
                    txn_date = datetime.strptime(txn_date, "%Y-%m-%d").date()
                except ValueError:
                    logger.warning("Invalid date format for txn %s; skipping.", txn_id)
                    continue

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

            merchant_name = txn.get("merchant_name") or "Unknown"
            merchant_type = txn.get("payment_meta", {}).get("payment_method") or "Unknown"
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
                        "Updated transaction %s for account %s", txn_id, account_label
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
                    "➕ Inserted new transaction %s for account %s", txn_id, account_label
                )
                updated = True

        db.session.commit()
        return updated

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Error refreshing transactions for account %s: %s", account_id, exc, exc_info=True
        )
        db.session.rollback()
        return False

    return updated
