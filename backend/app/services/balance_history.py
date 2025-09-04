"""
Balance History Service

This service calculates historical account balances by working backwards from
the current balance using transaction deltas, then stores the results in the
account_history SQL table for efficient retrieval.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.config import logger
from app.extensions import db
from app.models import Account, AccountHistory, Transaction
from app.utils.finance_utils import normalize_account_balance
from sqlalchemy import and_, desc, func


def resolve_account_by_any_id(identifier) -> Optional[Account]:
    """
    Resolve account by either numeric primary key or external account_id.

    Args:
        identifier: Either integer ID, string numeric ID, or external account_id

    Returns:
        Account object if found, None otherwise
    """
    # If identifier is numeric-like, try primary key first
    try:
        if isinstance(identifier, int) or (
            isinstance(identifier, str) and identifier.isdigit()
        ):
            acct = Account.query.get(int(identifier))
            if acct:
                return acct
    except Exception:
        pass

    # Fallback to external string account_id
    try:
        return Account.query.filter_by(account_id=str(identifier)).first()
    except Exception:
        return None


def calculate_daily_balances(
    account_id: str,
    current_balance: float,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[Dict]:
    """
    Calculate daily balances by working backwards from current balance.

    Args:
        account_id: Account identifier
        current_balance: Current account balance (normalized)
        start_date: Start date for calculation
        end_date: End date for calculation

    Returns:
        List of daily balance records with date and balance
    """

    logger.info(
        f"Calculating balances for {account_id} from {start_date} to {end_date}"
    )

    # Get all transactions in the date range, grouped by date
    tx_rows = (
        db.session.query(func.date(Transaction.date), func.sum(Transaction.amount))
        .filter(Transaction.account_id == account_id)
        .filter(Transaction.date >= start_date)
        .filter(Transaction.date <= end_date)
        .filter(
            (Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None))
        )
        .group_by(func.date(Transaction.date))
        .order_by(desc(func.date(Transaction.date)))  # Most recent first
        .all()
    )

    # Convert to dict for easier lookup
    daily_amounts = {row[0]: float(row[1] or 0) for row in tx_rows}

    # Calculate daily balances working backwards
    balance_records = []
    running_balance = current_balance

    current_date = end_date
    while current_date >= start_date:
        # Add today's balance
        balance_records.append({"date": current_date, "balance": running_balance})

        # If there were transactions on this date, subtract them to get previous balance
        if current_date in daily_amounts:
            running_balance -= daily_amounts[current_date]

        current_date -= timedelta(days=1)

    # Reverse to get chronological order
    balance_records.reverse()

    logger.info(f"Calculated {len(balance_records)} daily balance records")
    return balance_records


def store_balance_history(account_id: str, balance_records: List[Dict]) -> int:
    """
    Store balance history records in the database.

    Args:
        account_id: Account identifier
        balance_records: List of balance records to store

    Returns:
        Number of records processed
    """

    account = resolve_account_by_any_id(account_id)
    if not account:
        logger.warning(f"Balance history: account {account_id} not found (skipping)")
        return 0

    if not balance_records:
        return 0

    # Use the resolved account's account_id for consistency
    lookup_key = account.account_id

    # Get all existing records for this account to avoid any constraint issues
    existing_records = AccountHistory.query.filter(
        AccountHistory.account_id == lookup_key
    ).all()

    # Create lookup dict for existing records, normalizing dates to date objects
    existing_dates = {}
    for record in existing_records:
        # Handle both datetime and date objects
        record_date = record.date
        if hasattr(record_date, "date"):
            record_date = record_date.date()
        existing_dates[record_date] = record

    stored_count = 0
    updated_count = 0

    try:
        for record in balance_records:
            record_date = record["date"]

            if record_date in existing_dates:
                # Update existing record
                existing = existing_dates[record_date]
                existing.balance = record["balance"]
                existing.is_hidden = account.is_hidden or False
                updated_count += 1
            else:
                new_record = AccountHistory(
                    account_id=lookup_key,
                    user_id=account.user_id,
                    date=datetime.combine(
                        record_date, datetime.min.time(), tzinfo=timezone.utc
                    ),
                    balance=record["balance"],
                    is_hidden=account.is_hidden or False,
                )
                db.session.add(new_record)
                stored_count += 1

        db.session.commit()
        total_processed = stored_count + updated_count
        logger.info(
            f"Processed {total_processed} balance history records for {account_id} ({stored_count} new, {updated_count} updated)"
        )
        return total_processed

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to store balance history: {e}")
        return 0


def update_account_balance_history(
    account_id: str, days: int = 365, force_update: bool = False
) -> bool:
    """
    Update balance history for an account.

    Args:
        account_id: Account identifier
        days: Number of days to calculate history for
        force_update: Whether to force update even if recent data exists

    Returns:
        True if successful, False otherwise
    """

    try:
        account = resolve_account_by_any_id(account_id)
        if not account:
            logger.warning(
                f"Balance history: account {account_id} not found (skipping)"
            )
            return False

        # Use the resolved account's account_id for consistency
        lookup_key = account.account_id

        # Check if we need to update
        if not force_update:
            latest_record = (
                AccountHistory.query.filter_by(account_id=lookup_key)
                .order_by(desc(AccountHistory.date))
                .first()
            )

            if latest_record:
                # If we have data from today or yesterday, skip unless forced
                latest_date = latest_record.date
                if hasattr(latest_date, "date"):
                    latest_date = latest_date.date()
                days_old = (datetime.now().date() - latest_date).days
                if days_old <= 1:
                    logger.info(f"Balance history for {lookup_key} is up to date")
                    return True

        # Calculate date range
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days - 1)

        # Get normalized current balance
        current_balance = normalize_account_balance(account.balance, account.type)

        logger.info(
            f"Updating balance history for {account.name} ({account.id}/{account.account_id}) from {start_date} to {end_date}"
        )
        logger.info(
            f"Current balance: {account.balance} -> normalized: {current_balance}"
        )

        # Calculate balance history
        balance_records = calculate_daily_balances(
            lookup_key, current_balance, start_date, end_date
        )

        if not balance_records:
            logger.warning(f"No balance records calculated for {account_id}")
            return False

        # Store in database
        stored_count = store_balance_history(account_id, balance_records)

        if stored_count > 0:
            logger.info(f"Successfully updated balance history for {account_id}")
            return True
        else:
            logger.error(f"Failed to store balance history for {account_id}")
            return False

    except Exception as e:
        logger.error(
            f"Error updating balance history for {account_id}: {e}", exc_info=True
        )
        return False


def get_balance_history_from_db(account_id: str, days: int = 30) -> List[Dict]:
    """
    Retrieve balance history from the database.

    Args:
        account_id: Account identifier
        days: Number of days to retrieve

    Returns:
        List of balance records from database
    """

    # Resolve account to get the correct account_id
    account = resolve_account_by_any_id(account_id)
    if not account:
        logger.warning(f"Balance history: account {account_id} not found for retrieval")
        return []

    lookup_key = account.account_id

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=_tz.utc)
    end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=_tz.utc)

    records = (
        AccountHistory.query.filter(
            and_(
                AccountHistory.account_id == lookup_key,
                AccountHistory.date >= start_dt,
                AccountHistory.date <= end_dt,
            )
        )
        .order_by(AccountHistory.date)
        .all()
    )

    return [
        {
            "date": (
                record.date.date().isoformat()
                if hasattr(record.date, "date")
                else record.date
            ),
            "balance": record.balance,
        }
        for record in records
    ]


def update_all_accounts_balance_history(days: int = 365) -> Dict[str, bool]:
    """
    Update balance history for all accounts.

    Args:
        days: Number of days to calculate history for

    Returns:
        Dict mapping account_id to success status
    """

    results = {}
    accounts = Account.query.all()

    logger.info(f"Updating balance history for {len(accounts)} accounts")

    for account in accounts:
        try:
            success = update_account_balance_history(account.account_id, days)
            results[account.account_id] = success
        except Exception as e:
            logger.error(f"Failed to update {account.account_id}: {e}")
            results[account.account_id] = False

    successful = sum(1 for success in results.values() if success)
    logger.info(f"Updated balance history for {successful}/{len(accounts)} accounts")

    return results
