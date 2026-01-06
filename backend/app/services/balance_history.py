"""Balance history computations built on transactional deltas."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from app.config import logger
from app.extensions import db
from app.models import Account, AccountHistory, Transaction
from app.utils.finance_utils import normalize_account_balance
from dateutil import tz as _tz
from sqlalchemy import and_, desc, func

TWOPLACES = Decimal("0.01")


def _to_decimal(value) -> Decimal:
    """Return ``value`` as a Decimal rounded to two places."""

    if isinstance(value, Decimal):
        return value.quantize(TWOPLACES)
    return Decimal(str(value or 0)).quantize(TWOPLACES)


def resolve_account_by_any_id(identifier) -> Optional[Account]:
    """Resolve account by either numeric primary key or external account_id."""

    try:
        if isinstance(identifier, int) or (
            isinstance(identifier, str) and identifier.isdigit()
        ):
            acct = Account.query.get(int(identifier))
            if acct:
                return acct
    except Exception:
        pass

    try:
        return Account.query.filter_by(account_id=str(identifier)).first()
    except Exception:
        return None


def calculate_daily_balances(
    account_id: str,
    current_balance: Decimal,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[Dict]:
    """Calculate daily balances by working backwards from current balance."""

    logger.info(
        "Calculating balances for %s from %s to %s",
        account_id,
        start_date,
        end_date,
    )

    tx_rows = (
        db.session.query(func.date(Transaction.date), func.sum(Transaction.amount))
        .filter(Transaction.account_id == account_id)
        .filter(Transaction.date >= start_date)
        .filter(Transaction.date <= end_date)
        .filter(
            (Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None))
        )
        .group_by(func.date(Transaction.date))
        .order_by(desc(func.date(Transaction.date)))
        .all()
    )

    daily_amounts = {row[0]: _to_decimal(row[1] or 0) for row in tx_rows}

    balance_records: List[Dict] = []
    running_balance = _to_decimal(current_balance)

    current_date = end_date
    while current_date >= start_date:
        balance_records.append({"date": current_date, "balance": running_balance})

        if current_date in daily_amounts:
            running_balance = (running_balance - daily_amounts[current_date]).quantize(
                TWOPLACES
            )

        current_date -= timedelta(days=1)

    balance_records.reverse()
    logger.info("Calculated %d daily balance records", len(balance_records))
    return balance_records


def store_balance_history(account_id: str, balance_records: List[Dict]) -> int:
    """Store balance history records in the database."""

    account = resolve_account_by_any_id(account_id)
    if not account:
        logger.warning("Balance history: account %s not found (skipping)", account_id)
        return 0

    if not balance_records:
        return 0

    lookup_key = account.account_id
    existing_records = AccountHistory.query.filter(
        AccountHistory.account_id == lookup_key
    ).all()

    existing_dates = {}
    for record in existing_records:
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
            "Processed %d balance history records for %s (%d new, %d updated)",
            total_processed,
            account_id,
            stored_count,
            updated_count,
        )
        return total_processed

    except Exception as e:
        db.session.rollback()
        logger.error("Failed to store balance history: %s", e)
        return 0


def update_account_balance_history(
    account_id: str, days: int = 365, force_update: bool = False
) -> bool:
    """Update balance history for an account."""

    try:
        account = resolve_account_by_any_id(account_id)
        if not account:
            logger.warning(
                "Balance history: account %s not found (skipping)", account_id
            )
            return False

        lookup_key = account.account_id

        if not force_update:
            latest_record = (
                AccountHistory.query.filter_by(account_id=lookup_key)
                .order_by(desc(AccountHistory.date))
                .first()
            )

            if latest_record:
                latest_date = latest_record.date
                if hasattr(latest_date, "date"):
                    latest_date = latest_date.date()
                days_old = (datetime.now().date() - latest_date).days
                if days_old <= 1:
                    logger.info("Balance history for %s is up to date", lookup_key)
                    return True

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days - 1)

        current_balance = normalize_account_balance(
            account.balance, account.type, account_id=account.account_id
        )

        logger.info(
            "Updating balance history for %s (%s/%s) from %s to %s",
            account.name,
            account.id,
            account.account_id,
            start_date,
            end_date,
        )
        logger.info(
            "Current balance: %s -> normalized: %s",
            account.balance,
            current_balance,
        )

        balance_records = calculate_daily_balances(
            lookup_key, current_balance, start_date, end_date
        )

        if not balance_records:
            logger.warning("No balance records calculated for %s", account_id)
            return False

        stored_count = store_balance_history(account_id, balance_records)

        if stored_count > 0:
            logger.info("Successfully updated balance history for %s", account_id)
            return True
        logger.error("Failed to store balance history for %s", account_id)
        return False

    except Exception as e:
        logger.error(
            "Error updating balance history for %s: %s", account_id, e, exc_info=True
        )
        return False


def update_all_accounts_balance_history(
    days: int = 365, force_update: bool = False
) -> Dict[str, bool]:
    """Update balance history for every account in the system."""

    results: Dict[str, bool] = {}
    accounts = Account.query.all()

    for account in accounts:
        account_id = account.account_id
        try:
            results[account_id] = update_account_balance_history(
                account_id, days=days, force_update=force_update
            )
        except Exception as e:
            logger.error(
                "Error updating balance history for %s: %s",
                account_id,
                e,
                exc_info=True,
            )
            results[account_id] = False

    logger.info(
        "Balance history update completed: %d/%d accounts updated",
        sum(1 for success in results.values() if success),
        len(results),
    )
    return results


def get_balance_history_from_db(account_id: str, days: int = 30) -> List[Dict]:
    """Retrieve balance history from the database."""

    account = resolve_account_by_any_id(account_id)
    if not account:
        logger.warning(
            "Balance history: account %s not found for retrieval", account_id
        )
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
            "balance": float(
                _to_decimal(record.balance) if record.balance is not None else 0
            ),
        }
        for record in records
    ]
