import json
from datetime import date, datetime

import requests
from app.config import FILES, logger
from app.extensions import db
from app.models import Account, AccountDetails, AccountHistory, Transaction

RAW_FILE = FILES["TRANSACTIONS_RAW"]


def upsert_accounts(user_id, accounts_data):
    logger.debug(f"Upserting accounts for user {user_id}: {accounts_data}")
    for account in accounts_data:
        account_id = account.get("id")
        name = account.get("name") or "Unnamed Account"
        acc_type = account.get("type") or "Unknown"
        balance = account.get("balance", {}).get("current", 0) or 0
        subtype = account.get("subtype") or "Unknown"
        status = account.get("status") or "Unknown"
        institution = account.get("institution", {}) or {}
        institution_name = institution.get("name") or "Unknown"
        enrollment_id = account.get("enrollment_id") or ""
        refresh_links = account.get("links") or {}
        link_type = "Teller"  # Assuming these are Teller-linked

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
            db.session.flush()  # Ensure new_account gets an ID
            details = AccountDetails(
                account_id=account_id,
                enrollment_id=enrollment_id,
                refresh_links=json.dumps(refresh_links),
            )
            db.session.add(details)
        # Insert a historical record for today's refresh if not present
        today = date.today()
        existing_history = AccountHistory.query.filter_by(
            account_id=account_id, date=today
        ).first()
        if not existing_history:
            history_record = AccountHistory(
                account_id=account_id, date=today, balance=balance
            )
            db.session.add(history_record)
    db.session.commit()


def refresh_account_data_for_account(
    account, access_token, teller_dot_cert, teller_dot_key, teller_api_base_url
):
    updated = False
    now = datetime.utcnow()

    # Refresh balance using Teller's documented endpoint:
    url_balance = f"{teller_api_base_url}/accounts/{account.account_id}/balances"
    resp_balance = requests.get(
        url_balance, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )
    if resp_balance.status_code == 200:
        balance_data = resp_balance.json()
        print(balance_data)
        new_balance = (
            balance_data.get("balance", {}).get("current", account.balance) or 0
        )
        if new_balance != account.balance:
            logger.debug(
                f"Account {account.account_id}: Balance updated from {account.balance} to {new_balance}"
            )
            account.balance = new_balance
            updated = True
    else:
        logger.error(
            f"Failed to refresh balance for account {account.account_id}: {resp_balance.text}"
        )

    # Refresh transactions using Teller's documented endpoint:
    url_txns = f"{teller_api_base_url}/accounts/{account.account_id}/transactions"
    resp_txns = requests.get(
        url_txns, cert=(teller_dot_cert, teller_dot_key), auth=(access_token, "")
    )
    if resp_txns.status_code == 200:
        txns_data = resp_txns.json()
        with open(RAW_FILE, "w") as f:
            json.dump(txns_data, f, indent=4)
        print(txns_data)
        for txn in txns_data:
            txn_id = txn.get("id")
            existing_txn = None
            try:
                from app.models import Transaction

                existing_txn = Transaction.query.filter_by(
                    transaction_id=txn_id
                ).first()
            except Exception as ex:
                logger.error(f"Error querying transaction {txn_id}: {ex}")
            # Extract extra fields with defaults:
            details = txn.get("details", {}) or {}
            category = details.get("category")
            if isinstance(category, list) and category:
                category = category[-1] or "Unknown"
            else:
                category = category or "Unknown"
            if existing_txn:
                existing_txn.amount = txn.get("amount") or 0
                existing_txn.date = txn.get("date") or ""
                existing_txn.description = txn.get("description") or ""
                existing_txn.category = ("category") or ""
                existing_txn.details = txn.get("details") or ""
            else:
                new_txn = Transaction(
                    transaction_id=txn_id,
                    account_id=account.account_id,
                    amount=txn.get("amount") or 0,
                    date=txn.get("date") or "",
                    description=txn.get("description") or "",
                )
                db.session.add(new_txn)
        updated = True
    else:
        logger.error(
            f"Failed to refresh transactions for account {account.account_id}: {resp_txns.text}"
        )

    # Update last_refreshed timestamp
    account.last_refreshed = now

    # Insert a historical record for today's refresh if not present
    from app.models import AccountHistory

    today = date.today()
    existing_history = AccountHistory.query.filter_by(
        account_id=account.account_id, date=today
    ).first()
    if not existing_history:
        history_record = AccountHistory(
            account_id=account.account_id, date=today, balance=account.balance
        )
        db.session.add(history_record)
        updated = True

    return updated


def get_paginated_transactions(page, page_size):
    query = Transaction.query.order_by(Transaction.date.desc())
    total = query.count()
    txns = query.offset((page - 1) * page_size).limit(page_size).all()
    serialized = [
        {
            "transaction_id": t.transaction_id,
            "account_id": t.account_id,
            "amount": t.amount,
            "date": t.date,
            "description": t.description,
            "category": t.category,
            "merchant_name": t.merchant_name,
            "merchant_typ": t.merchant_typ,
        }
        for t in txns
    ]
    return serialized, total
