"""Database persistence and refresh helpers for account data."""

import json
from datetime import date as pydate
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from app.config import FILES, logger
from app.extensions import db
from app.helpers.normalize import normalize_amount
from app.helpers.plaid_helpers import get_accounts, get_transactions
from app.models import Account, AccountHistory, Category, PlaidAccount, Transaction
from app.sql import transaction_rules_logic
from app.sql.dialect_utils import dialect_insert
from app.sql.refresh_metadata import refresh_or_insert_plaid_metadata
from app.utils.finance_utils import display_transaction_amount
from plaid import ApiException
from sqlalchemy import case, func
from sqlalchemy.orm import aliased

ParentCategory = aliased(Category)

TRANSACTIONS_RAW = FILES["LAST_TX_REFRESH"]
TRANSACTIONS_RAW_ENRICHED = FILES["TRANSACTIONS_RAW_ENRICHED"]

# Valid account status values stored in the database enum.
ALLOWED_ACCOUNT_STATUSES = {"active", "inactive", "closed", "archived"}


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


def normalize_account_status(status: Optional[str]) -> str:
    """Return an account status compatible with the database enum."""

    if isinstance(status, str):
        candidate = status.strip().lower()
        if candidate in ALLOWED_ACCOUNT_STATUSES:
            return candidate

    return "active"


def detect_internal_transfer(
    txn, date_epsilon: int = 1, amount_epsilon: Decimal = Decimal("0.01")
) -> None:
    """Flag ``txn`` and a matching counterpart as an internal transfer.

    A counterpart is any transaction for the same user in a different account
    with an equal and opposite amount within ``date_epsilon`` days. The
    closest date match is selected when multiple candidates exist. Monetary
    comparisons use ``Decimal`` values to avoid floating point drift.
    """

    account = Account.query.filter_by(account_id=txn.account_id).first()
    if not account or txn.is_internal:
        return

    # Normalize to date for robust comparisons (handles datetime/date mix)
    txn_base_date = txn.date.date() if hasattr(txn.date, "date") else txn.date
    start = txn_base_date - timedelta(days=date_epsilon)
    end = txn_base_date + timedelta(days=date_epsilon)

    candidates = (
        db.session.query(Transaction)
        .join(Account, Transaction.account_id == Account.account_id)
        .filter(Account.user_id == account.user_id)
        .filter(Transaction.account_id != txn.account_id)
        .filter(Transaction.date >= start)
        .filter(Transaction.date <= end)
        .filter(func.abs(Transaction.amount + txn.amount) <= amount_epsilon)
        .filter(Transaction.is_internal.is_(False))
        .all()
    )

    best = None
    best_diff = None
    for other in candidates:
        # Compute diff in days using normalized dates
        other_base_date = (
            other.date.date() if hasattr(other.date, "date") else other.date
        )
        diff = abs((txn_base_date - other_base_date).days)
        if best is None or diff < best_diff:
            best = other
            best_diff = diff

    if best:
        txn.is_internal = True
        txn.internal_match_id = best.transaction_id
        best.is_internal = True
        best.internal_match_id = txn.transaction_id


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
                "balance": float(acc.balance) if acc.balance is not None else None,
                "status": acc.status,
            }
        )
    return accounts


def save_plaid_account(account_id, item_id, access_token, product):
    """Insert or update a :class:`PlaidAccount` row."""

    plaid_acct = PlaidAccount.query.filter_by(account_id=account_id).first()
    if plaid_acct:
        plaid_acct.access_token = access_token
        plaid_acct.item_id = item_id
        plaid_acct.product = product
        plaid_acct.updated_at = datetime.now(timezone.utc)
    else:
        plaid_acct = PlaidAccount(
            account_id=account_id,
            access_token=access_token,
            item_id=item_id,
            product=product,
        )
        db.session.add(plaid_acct)
    db.session.commit()
    return plaid_acct


def upsert_accounts(user_id, account_list, provider, access_token=None):
    processed_ids = set()
    count = 0
    logger.debug("[CHECK] upsert_accounts received user_id=%s", user_id)

    for account in account_list:
        try:
            account_id = account.get("account_id") or account.get("id")
            if not account_id or account_id in processed_ids:
                logger.warning(
                    "Skipping invalid or duplicate account id: %s", account_id
                )
                continue
            processed_ids.add(account_id)

            name = account.get("name") or "Unnamed Account"
            acc_type = str(account.get("type") or "Unknown")

            # ✅ Corrected Plaid balance parsing
            balance_raw = (
                account.get("balances", {}).get("current")
                or account.get("balance", {}).get("current")
                or account.get("balance")
                or 0
            )
            balance = normalize_balance(balance_raw, acc_type)
            logger.debug("[UPSERT] Balance parsed for %s: %s", account_id, balance)

            subtype = str(account.get("subtype") or "Unknown").capitalize()
            status = normalize_account_status(account.get("status"))
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
                        "Failed to refresh institution for %s: %s",
                        account_id,
                        e,
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
                # Normalize provider/link type to lowercase to match DB enum values
                "link_type": str(provider or "").lower() or "manual",
            }

            existing_account = Account.query.filter_by(account_id=account_id).first()
            if existing_account:
                logger.debug("Updating account %s", account_id)
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
                logger.debug("Creating new account %s", account_id)
                new_account = Account(**filtered_account)
                db.session.add(new_account)

            # Existing AccountHistory logic follows...

            # Patched: safely upsert AccountHistory with conflict resolution
            now_utc = datetime.now(timezone.utc)
            today = now_utc.date()
            dt_today = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
            stmt = dialect_insert(AccountHistory).values(
                account_id=account_id,
                user_id=user_id,
                date=dt_today,
                balance=balance,
                created_at=now_utc,
                updated_at=now_utc,
            )

            on_conflict = getattr(stmt, "on_conflict_do_update", None)
            if callable(on_conflict):
                stmt = on_conflict(
                    index_elements=["account_id", "date"],
                    set_={
                        "balance": balance,
                        "updated_at": now_utc,
                    },
                )
                db.session.execute(stmt)
            else:
                history = AccountHistory.query.filter_by(
                    account_id=account_id, date=dt_today
                ).first()
                if history:
                    history.balance = balance
                    history.updated_at = now_utc
                else:
                    db.session.add(
                        AccountHistory(
                            account_id=account_id,
                            user_id=user_id,
                            date=dt_today,
                            balance=balance,
                            created_at=now_utc,
                            updated_at=now_utc,
                        )
                    )

            count += 1
            if count % 100 == 0:
                db.session.commit()
                logger.debug("Committed batch of 100 accounts.")

        except Exception as e:
            logger.error(
                "Failed to upsert account %s: %s",
                account_id,
                e,
                exc_info=True,
            )

    db.session.commit()
    logger.info("Finished upserting accounts.")


def get_paginated_transactions(
    page,
    page_size,
    start_date=None,
    end_date=None,
    category=None,
    user_id=None,
    account_id=None,
    account_ids=None,
    tx_type=None,
    recent=False,
    limit=None,
    include_running_balance=False,
):
    """Return paginated transaction rows with optional filtering.

    Parameters
    ----------
    page, page_size : int
        Pagination controls.
    start_date, end_date : datetime, optional
        Bound the query to a date range.
    category : str, optional
        Filter by transaction category string.
    user_id : str, optional
        Scope results to a specific user.
    account_id : str, optional
        Legacy single-account filter.
    account_ids : list[str], optional
        Filter by one or more account identifiers.
    tx_type : str, optional
        ``"credit"`` or ``"debit"`` to filter by amount sign.
    recent : bool, default False
        If ``True`` limit results to the newest records ignoring pagination.
    limit : int, optional
        Maximum number of rows when ``recent`` is ``True``.
    include_running_balance : bool, default False
        When ``True``, include a per-transaction running balance computed with a window
        function so pagination does not require loading every row into memory.
    """

    query = (
        db.session.query(Transaction, Account, Category)
        .join(Account, Transaction.account_id == Account.account_id)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(Account.is_hidden.is_(False))
        .filter(
            (Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None))
        )
        .order_by(Transaction.date.desc(), Transaction.transaction_id.desc())
    )

    if user_id:
        query = query.filter(Account.user_id == user_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if category:
        query = query.filter(Transaction.category == category)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if account_ids:
        query = query.filter(Transaction.account_id.in_(account_ids))
    if tx_type == "credit":
        query = query.filter(Transaction.amount > 0)
    elif tx_type == "debit":
        query = query.filter(Transaction.amount < 0)

    total = query.order_by(None).count()
    offset = (page - 1) * page_size

    running_balance_expr = None
    if include_running_balance:
        running_balance_expr = _running_balance_expression()
        balance_query = query.add_columns(running_balance_expr.label("running_balance"))
        if recent:
            results = balance_query.limit(limit or page_size).all()
        else:
            results = balance_query.offset(offset).limit(page_size).all()
    elif recent:
        results = query.limit(limit or page_size).all()
    else:
        results = query.offset(offset).limit(page_size).all()

    # Unpack and serialize
    serialized = []
    for row in results:
        if running_balance_expr is not None:
            txn, acc, cat, running_balance = row
        else:
            txn, acc, cat = row
            running_balance = None
        # Prefer stored txn.category; fall back to joined Category.display_name
        category_label = txn.category
        if not category_label and cat and getattr(cat, "display_name", None):
            category_label = cat.display_name

        serialized.append(
            {
                "transaction_id": txn.transaction_id,
                "date": txn.date.isoformat() if txn.date else None,
                "amount": display_transaction_amount(txn),
                "description": txn.description or txn.merchant_name or "N/A",
                "category": category_label or "Uncategorized",
                "category_id": getattr(cat, "id", None),
                "category_icon_url": getattr(cat, "pfc_icon_url", None),
                "merchant_name": txn.merchant_name or "Unknown",
                "user_id": getattr(txn, "user_id", None)
                or getattr(acc, "user_id", None),
                "account_name": acc.name or "Unnamed Account",
                "institution_name": acc.institution_name or "Unknown",
                "subtype": acc.subtype or "Unknown",
                "account_id": acc.account_id or "Unknown",
                "pending": getattr(txn, "pending", False),
                "isEditing": False,
                "running_balance": (
                    float(running_balance) if running_balance is not None else None
                ),
            }
        )

    return serialized, total


def _running_balance_expression():
    """Build a window expression for per-transaction running balances.

    The expression starts from the normalized account balance (assets positive,
    liabilities negative) and walks backwards through transactions ordered by
    posting date so each row returns the balance immediately after that
    transaction.
    """

    account_type = func.lower(func.coalesce(Account.type, Account.subtype, "asset"))
    balance_value = func.coalesce(Account.balance, 0)
    normalized_balance = case(
        (
            account_type.in_(
                ("credit card", "credit", "loan", "liability"),
            ),
            -balance_value,
        ),
        else_=func.abs(balance_value),
    )

    signed_amount = case(
        (Transaction.transaction_type == "income", func.abs(Transaction.amount)),
        (Transaction.transaction_type == "expense", -func.abs(Transaction.amount)),
        else_=-Transaction.amount,
    )

    cumulative_delta = func.coalesce(
        func.sum(signed_amount).over(
            partition_by=Transaction.account_id,
            order_by=[Transaction.date.desc(), Transaction.transaction_id.desc()],
            rows=(None, -1),
        ),
        0,
    )

    return normalized_balance - cumulative_delta


def get_balance_at(account_id: str, target_date: pydate) -> Optional[float]:
    """Return the balance for ``account_id`` on ``target_date``.

    Args:
        account_id: External account identifier.
        target_date: Date to fetch the balance for.

    Returns:
        Balance as ``float`` if a snapshot exists, otherwise ``None``.
    """

    row = (
        AccountHistory.query.filter(AccountHistory.account_id == account_id)
        .filter(AccountHistory.date == target_date)
        .with_entities(AccountHistory.balance)
        .first()
    )
    if not row:
        return None
    balance = getattr(row, "balance", row[0])
    return float(balance)


def get_net_change(account_id: str, start_date: pydate, end_date: pydate) -> dict:
    """Compute net balance change between two dates.

    Fetches balances at ``start_date`` and ``end_date`` and returns their
    difference as ``end_balance - start_balance``.

    Args:
        account_id: External account identifier.
        start_date: Beginning of the period.
        end_date: End of the period.

    Returns:
        Dictionary with account_id, net_change, and period metadata.

    Raises:
        ValueError: If a balance snapshot is missing for either date.
    """

    start_balance = get_balance_at(account_id, start_date)
    end_balance = get_balance_at(account_id, end_date)
    if start_balance is None or end_balance is None:
        raise ValueError("Balance missing for start_date or end_date")

    return {
        "account_id": account_id,
        "net_change": end_balance - start_balance,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
    }


def get_or_create_category(primary, detailed, pfc_primary, pfc_detailed, pfc_icon_url):
    """
    Ensures no duplicate (primary, detailed). Returns the correct Category row.
    """
    # Try PFC first
    category = (
        db.session.query(Category)
        .filter_by(pfc_primary=pfc_primary, pfc_detailed=pfc_detailed)
        .first()
    )
    # Fallback legacy
    if not category:
        category = (
            db.session.query(Category)
            .filter_by(primary_category=primary, detailed_category=detailed)
            .first()
        )
    # If another Category exists for this (primary, detailed), use it instead of updating!
    if category and (
        category.primary_category != primary or category.detailed_category != detailed
    ):
        duplicate = (
            db.session.query(Category)
            .filter_by(primary_category=primary, detailed_category=detailed)
            .first()
        )
        if duplicate and duplicate.id != category.id:
            return duplicate  # point to the duplicate!
    if not category:
        category = Category(
            primary_category=primary,
            detailed_category=detailed,
            pfc_primary=pfc_primary,
            pfc_detailed=pfc_detailed,
            pfc_icon_url=pfc_icon_url,
            display_name=f"{pfc_primary} > {pfc_detailed}",
        )
        db.session.add(category)
        db.session.flush()
    else:
        # Update icon/display if changed, not primary/detailed if it would collide
        if pfc_icon_url and category.pfc_icon_url != pfc_icon_url:
            category.pfc_icon_url = pfc_icon_url
        display_name = f"{pfc_primary} > {pfc_detailed}"
        if category.display_name != display_name:
            category.display_name = display_name
    return category


def refresh_data_for_plaid_account(
    access_token, account_id, start_date=None, end_date=None
):
    """Refresh a single Plaid account and return update status and error info.

    Parameters are the same as before, but the return value is now a tuple of
    ``(updated, error)`` where ``error`` is ``None`` on success or a mapping with
    ``plaid_error_code`` and ``plaid_error_message`` when an exception is raised
    by the Plaid client.
    """
    updated = False
    now = datetime.now(timezone.utc)

    PLAID_MAX_LOOKBACK_DAYS = 680
    end_date_obj = end_date or now.date()
    start_date_obj = (
        start_date or (now - timedelta(days=PLAID_MAX_LOOKBACK_DAYS)).date()
    )

    if isinstance(end_date_obj, str):
        end_date_obj = datetime.strptime(end_date_obj, "%Y-%m-%d").date()
    if isinstance(start_date_obj, str):
        start_date_obj = datetime.strptime(start_date_obj, "%Y-%m-%d").date()

    try:
        account = Account.query.filter_by(account_id=account_id).first()
        if not account:
            logger.warning("[DB Lookup] No account found for account_id=%s", account_id)
            return False

        # Refresh balance
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
        # Apply user-defined rules before upserting, with robust normalization
        normalized = []
        for tx in transactions:
            tx = dict(tx)
            # Some Plaid sandboxes can return category=None; normalize to list
            if tx.get("category") is None:
                tx["category"] = []
            normalized.append(transaction_rules_logic.apply_rules(account.user_id, tx))
        transactions = normalized

        fetched_count = len(transactions)

        # Only process transactions for this specific account
        transactions = [
            txn for txn in transactions if txn.get("account_id") == account_id
        ]

        plaid_account_obj = PlaidAccount.query.filter_by(account_id=account_id).first()

        totals = {
            "processed": 0,
            "inserted": 0,
            "updated": 0,
            "unchanged": 0,
            "skipped_missing_id": 0,
            "skipped_invalid_date": 0,
        }

        for txn in transactions:
            txn_id = txn.get("transaction_id")
            if not txn_id:
                totals["skipped_missing_id"] += 1
                continue

            txn_date = txn.get("date")
            # Normalize txn_date to timezone-aware datetime for the DB model
            if isinstance(txn_date, str):
                try:
                    parsed_date = datetime.strptime(txn_date, "%Y-%m-%d").date()
                    txn_date = datetime.combine(
                        parsed_date, datetime.min.time(), tzinfo=timezone.utc
                    )
                except ValueError:
                    totals["skipped_invalid_date"] += 1
                    continue
            elif isinstance(txn_date, pydate) and not isinstance(txn_date, datetime):
                txn_date = datetime.combine(
                    txn_date, datetime.min.time(), tzinfo=timezone.utc
                )

            # Plaid PFC fields
            pfc_obj = txn.get("personal_finance_category", {})
            pfc_primary = pfc_obj.get("primary") or "Unknown"
            pfc_detailed = pfc_obj.get("detailed") or "Unknown"
            pfc_icon_url = txn.get("personal_finance_category_icon_url")

            # Legacy Plaid category
            category_path = txn.get("category", [])
            if not isinstance(category_path, (list, tuple)):
                category_path = []
            primary = category_path[0] if len(category_path) > 0 else "Unknown"
            detailed = category_path[1] if len(category_path) > 1 else "Unknown"

            # Use robust category upsert logic
            category = get_or_create_category(
                primary, detailed, pfc_primary, pfc_detailed, pfc_icon_url
            )

            merchant_name = txn.get("merchant_name") or "Unknown"
            merchant_type = (
                txn.get("payment_meta", {}).get("payment_method") or "Unknown"
            )
            description = txn.get("name") or "[no description]"
            pending = txn.get("pending", False)
            txn_amount = process_transaction_amount(txn.get("amount") or 0)

            existing_txn = Transaction.query.filter_by(transaction_id=txn_id).first()

            totals["processed"] += 1

            if existing_txn:
                needs_update = (
                    existing_txn.amount != txn_amount
                    or existing_txn.date != txn_date
                    or existing_txn.description != description
                    or existing_txn.pending != pending
                    or existing_txn.category_id != category.id
                    or existing_txn.merchant_name != merchant_name
                    or existing_txn.merchant_type != merchant_type
                )
                if needs_update:
                    existing_txn.amount = txn_amount
                    existing_txn.date = txn_date
                    existing_txn.description = description
                    existing_txn.pending = pending
                    existing_txn.category_id = category.id
                    existing_txn.category = category.display_name
                    existing_txn.merchant_name = merchant_name
                    existing_txn.merchant_type = merchant_type
                    existing_txn.provider = "plaid"
                    existing_txn.personal_finance_category = pfc_obj or None
                    existing_txn.personal_finance_category_icon_url = pfc_icon_url
                    totals["updated"] += 1
                    updated = True
                else:
                    totals["unchanged"] += 1
                # -- Update Plaid metadata on every refresh (even if not updating Transaction) --
                if plaid_account_obj:
                    refresh_or_insert_plaid_metadata(
                        txn, existing_txn, plaid_account_obj.account_id
                    )
                detect_internal_transfer(existing_txn)
            else:
                new_txn = Transaction(
                    transaction_id=txn_id,
                    amount=txn_amount,
                    date=txn_date,
                    description=description,
                    pending=pending,
                    account_id=account_id,
                    category_id=category.id,
                    category=category.display_name,
                    merchant_name=merchant_name,
                    merchant_type=merchant_type,
                    provider="plaid",
                    personal_finance_category=pfc_obj or None,
                    personal_finance_category_icon_url=pfc_icon_url,
                )
                db.session.add(new_txn)
                totals["inserted"] += 1
                updated = True
                if plaid_account_obj:
                    refresh_or_insert_plaid_metadata(
                        txn, new_txn, plaid_account_obj.account_id
                    )
                detect_internal_transfer(new_txn)

        db.session.commit()
        logger.info(
            (
                "[REFRESH] Account %s | fetched=%d | processed=%d | "
                "inserted=%d | updated=%d | unchanged=%d | "
                "skipped_missing_id=%d | skipped_invalid_date=%d"
            ),
            account_label,
            fetched_count,
            totals["processed"],
            totals["inserted"],
            totals["updated"],
            totals["unchanged"],
            totals["skipped_missing_id"],
            totals["skipped_invalid_date"],
        )
        return updated, None

    except ApiException as e:
        try:
            plaid_err = json.loads(e.body or "{}")
        except json.JSONDecodeError:
            plaid_err = {}
        plaid_error_code = plaid_err.get("error_code", "unknown")
        plaid_error_message = plaid_err.get("error_message", str(e))
        institution = getattr(account, "institution_name", "Unknown")
        account_name = getattr(account, "name", account_id)
        logger.error(
            "Plaid error refreshing transactions for %s / %s: %s - %s",
            institution,
            account_name,
            plaid_error_code,
            plaid_error_message,
            exc_info=True,
        )
        db.session.rollback()
        return False, {
            "plaid_error_code": plaid_error_code,
            "plaid_error_message": plaid_error_message,
        }

    except Exception as e:
        logger.error(
            "Error refreshing transactions for account %s: %s",
            account_id,
            e,
            exc_info=True,
        )
        db.session.rollback()
        return False, {
            "plaid_error_code": getattr(e, "code", "unknown"),
            "plaid_error_message": str(e),
        }

    return updated, None
