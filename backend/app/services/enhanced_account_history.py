"""Enhanced account history service with caching and pre-computation."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List

from app.extensions import db
from app.models import Account, AccountHistory, Transaction
from app.services.account_history import compute_balance_history
from app.utils.finance_utils import normalize_account_balance
from sqlalchemy import func

TWOPLACES = Decimal("0.01")


def get_or_compute_account_history(
    account_id: str, days: int = 30, force_recompute: bool = False
) -> List[Dict[str, float]]:
    """Get account balance history, using cached data when possible."""

    try:
        account = Account.query.filter_by(account_id=account_id).first()
        if not account:
            return []

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days - 1)

        if not force_recompute:
            cached_history = get_cached_history(account_id, start_date, end_date)
            if cached_history:
                return cached_history

        current_balance = normalize_account_balance(account.balance, account.type)
        fresh_history = compute_fresh_history(
            account_id, current_balance, start_date, end_date
        )

        if fresh_history:
            cache_history(account_id, account.user_id, fresh_history)

        return fresh_history

    except Exception as e:
        print(f"Error in get_or_compute_account_history: {e}")
        return []


def get_cached_history(account_id: str, start: date, end: date):
    records = (
        AccountHistory.query.filter(AccountHistory.account_id == account_id)
        .filter(AccountHistory.date >= start)
        .filter(AccountHistory.date <= end)
        .order_by(AccountHistory.date)
        .all()
    )
    if len(records) != (end - start).days + 1:
        return None

    latest_record = max(records, key=lambda r: r.updated_at)
    if latest_record.updated_at < datetime.now(timezone.utc) - timedelta(days=1):
        return None

    return [
        {
            "date": record.date.isoformat()
            if hasattr(record.date, "isoformat")
            else str(record.date),
            "balance": round(float(record.balance or 0), 2),
        }
        for record in records
    ]


def compute_fresh_history(
    account_id: str, current_balance: Decimal, start_date: date, end_date: date
) -> List[Dict[str, float]]:
    """Compute fresh balance history from transactions."""

    try:
        tx_rows = (
            db.session.query(func.date(Transaction.date), func.sum(Transaction.amount))
            .filter(Transaction.account_id == account_id)
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .filter(
                (Transaction.is_internal.is_(False))
                | (Transaction.is_internal.is_(None))
            )
            .group_by(func.date(Transaction.date))
            .all()
        )

        transactions = [
            {"date": row[0], "amount": float(row[1] or 0)} for row in tx_rows
        ]

        return compute_balance_history(
            float(current_balance), transactions, start_date, end_date
        )

    except Exception as e:
        print(f"Error computing fresh history: {e}")
        return []


def cache_history(account_id: str, user_id: str, history: List[Dict[str, float]]):
    """Cache balance history in the database for future retrieval."""

    try:
        now = datetime.now(timezone.utc)

        AccountHistory.query.filter(AccountHistory.account_id == account_id).delete()

        history_records = []
        for record in history:
            record_date = datetime.fromisoformat(record["date"]).date()
            balance_value = Decimal(str(record["balance"]))
            history_record = AccountHistory(
                account_id=account_id,
                user_id=user_id,
                date=record_date,
                balance=balance_value.quantize(TWOPLACES),
                is_hidden=False,
                created_at=now,
                updated_at=now,
            )
            history_records.append(history_record)

        db.session.add_all(history_records)
        db.session.commit()

        print(
            f"Cached {len(history_records)} balance history records for account {account_id}"
        )

    except Exception as e:
        print(f"Error caching history: {e}")
        db.session.rollback()


def update_account_balance_history(account_id: str, force_update: bool = False):
    """Update the cached balance history for an account."""

    try:
        for days in [7, 30, 90, 365]:
            get_or_compute_account_history(account_id, days=days, force_recompute=True)

        print(f"Updated balance history cache for account {account_id}")

    except Exception as e:
        print(f"Error updating account balance history: {e}")
