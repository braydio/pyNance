"""Database persistence and refresh helpers for account data."""

import json
import time
from datetime import date as pydate
from datetime import datetime, timedelta, timezone
from tempfile import NamedTemporaryFile

import requests
from app.config import FILES, logger
from app.extensions import db
from app.helpers.normalize import normalize_amount
from app.helpers.plaid_helpers import (
    get_accounts,
    get_transactions,
)
from app.models import (
    Account,
    AccountHistory,
    Category,
    Transaction,
)
from app.utils.finance_utils import normalize_transaction_amount
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import aliased

# Import transaction refresh helpers from the dedicated module for backward
# compatibility while routes transition to ``transactions_logic``.
from .transactions_logic import (
    fetch_url_with_backoff,
    get_paginated_transactions,
    refresh_data_for_plaid_account,
    refresh_data_for_teller_account,
)

ParentCategory = aliased(Category)

TRANSACTIONS_RAW = FILES["LAST_TX_REFRESH"]
TRANSACTIONS_RAW_ENRICHED = FILES["TRANSACTIONS_RAW_ENRICHED"]


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


def get_accounts_from_db(include_hidden: bool = False):
    """Return serialized account rows from the database."""
    query = Account.query
    if not include_hidden:
        query = query.filter(Account.is_hidden.is_(False))

    accounts = []
    for acc in query.all():
        accounts.append(
            {
                "account_id": acc.account_id,
                "user_id": acc.user_id,
                "name": acc.name,
                "type": acc.type,
                "subtype": acc.subtype,
                "institution_name": acc.institution_name,
                "balance": acc.balance,
                "status": acc.status,
            }
        )
    return accounts


def save_plaid_item(user_id, item_id, access_token, institution_name, product):
    item = PlaidItem.query.filter_by(item_id=item_id).first()
    if item:
        item.access_token = access_token
        item.institution_name = institution_name
        item.updated_at = datetime.now(timezone.utc)
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


def upsert_accounts(user_id, account_list, provider, access_token=None):
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

            # ✅ Corrected Plaid/Teller-safe balance parsing
            balance_raw = (
                account.get("balances", {}).get("current")
                or account.get("balance", {}).get("current")
                or account.get("balance")
                or 0
            )
            balance = normalize_balance(balance_raw, acc_type)
            logger.debug(f"[UPSERT] Balance parsed for {account_id}: {balance}")

            subtype = str(account.get("subtype") or "Unknown").capitalize()
            status = account.get("status") or "Unknown"
            institution_name = (
                (account.get("institution") or {}).get("name")
                or account.get("institution_name")
                or "Unknown"
            )

            # If we have access_token and missing institution, refresh metadata
            if access_token and institution_name == "Unknown":
                try:
                    refreshed_accounts = get_accounts(access_token, user_id)
                    for refreshed in refreshed_accounts:
                        if refreshed.get("account_id") == account_id:
                            institution_name = (
                                (refreshed.get("institution") or {}).get("name")
                                or refreshed.get("institution_name")
                                or institution_name
                            )
                            break
                except Exception as e:
                    logger.warning(
                        f"Failed to refresh institution for {account_id}: {e}"
                    )
            now = datetime.now(timezone.utc)
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
                    # Only update institution_name if it was Unknown
                    if (
                        key == "institution_name"
                        and existing_account.institution_name != "Unknown"
                    ):
                        continue
                    setattr(existing_account, key, value)
                existing_account.updated_at = now

            else:
                logger.debug(f"Creating new account {account_id}")
                new_account = Account(**filtered_account)
                db.session.add(new_account)

            # Existing AccountHistory logic follows...

            # Patched: safely upsert AccountHistory with conflict resolution
            today = datetime.now(timezone.utc).date()
            stmt = (
                insert(AccountHistory)
                .values(
                    account_id=account_id,
                    user_id=user_id,
                    date=today,
                    balance=balance,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                .on_conflict_do_update(
                    index_elements=["account_id", "date"],
                    set_={
                        "balance": balance,
                        "updated_at": datetime.now(timezone.utc),
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


