"""Enhanced account history service with caching and pre-computation."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from app.extensions import db
from app.models import Account, AccountHistory, Transaction
from app.services.account_history import compute_balance_history
from app.utils.finance_utils import normalize_account_balance
from sqlalchemy import func

TWOPLACES = Decimal("0.01")


def _ensure_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Return an aware UTC datetime for comparison."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_or_compute_account_history(
    account_id: str,
    days: int = 30,
    force_recompute: bool = False,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_internal: bool = False,
) -> List[Dict[str, float]]:
    """Get account balance history, using cached data when possible.

    Args:
        account_id: Account business identifier.
        days: Window length used when ``start_date`` and ``end_date`` are omitted.
        force_recompute: Skip cache read and recompute from transactions.
        start_date: Optional lower bound for the requested history window.
        end_date: Optional upper bound for the requested history window.
        include_internal: Include transfer-classified transactions when ``True``.

    Returns:
        Daily balances in ascending date order for the requested window.
    """

    try:
        account = Account.query.filter_by(account_id=account_id).first()
        if not account:
            return []

        resolved_end_date = end_date or datetime.now(timezone.utc).date()
        resolved_start_date = start_date or (
            resolved_end_date - timedelta(days=days - 1)
        )

        if resolved_start_date > resolved_end_date:
            return []

        if not force_recompute and not include_internal:
            cached_history = get_cached_history(
                account_id,
                resolved_start_date,
                resolved_end_date,
            )
            if cached_history:
                return cached_history

        current_balance = normalize_account_balance(
            account.balance, account.type, account_id=account.account_id
        )
        fresh_history = compute_fresh_history(
            account_id,
            current_balance,
            resolved_start_date,
            resolved_end_date,
            include_internal=include_internal,
        )

        if fresh_history and not include_internal:
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
    latest_updated_at = _ensure_utc(latest_record.updated_at)
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    if latest_updated_at is None or latest_updated_at < cutoff:
        return None

    return [
        {
            "date": (
                record.date.isoformat()
                if hasattr(record.date, "isoformat")
                else str(record.date)
            ),
            "balance": round(float(record.balance or 0), 2),
        }
        for record in records
    ]


def get_daily_transaction_totals(
    account_id: str,
    start_date: date,
    end_date: date,
    include_internal: bool = False,
) -> List[Dict[str, Decimal]]:
    """Return daily transaction totals for an account over a bounded range.

    Args:
        account_id: Account business identifier.
        start_date: Earliest transaction date to include.
        end_date: Latest transaction date to include.
        include_internal: Include transfer-classified transactions when ``True``.

    Returns:
        A list of dictionaries containing ``date`` and decimal ``amount`` values.
    """

    query = (
        db.session.query(func.date(Transaction.date), func.sum(Transaction.amount))
        .filter(Transaction.account_id == account_id)
        .filter(Transaction.date >= start_date)
        .filter(Transaction.date <= end_date)
    )

    if not include_internal:
        query = query.filter(
            (Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None))
        )

    tx_rows = query.group_by(func.date(Transaction.date)).all()
    return [{"date": row[0], "amount": row[1] or Decimal("0")} for row in tx_rows]


def compute_fresh_history(
    account_id: str,
    current_balance: Decimal,
    start_date: date,
    end_date: date,
    include_internal: bool = False,
) -> List[Dict[str, float]]:
    """Compute fresh balance history from transactions.

    Args:
        account_id: Account business identifier.
        current_balance: Known balance for ``end_date``.
        start_date: Earliest date included in the output.
        end_date: Latest date included in the output.
        include_internal: Include transfer-classified transactions when ``True``.
    """
    try:
        transactions = get_daily_transaction_totals(
            account_id,
            start_date,
            end_date,
            include_internal=include_internal,
        )

        return compute_balance_history(
            Decimal(str(current_balance)), transactions, start_date, end_date
        )

    except Exception as e:
        print(f"Error computing fresh history: {e}")
        return []


def cache_history(account_id: str, user_id: str, history: List[Dict[str, float]]):
    """Cache balance history with non-destructive date-window upserts.

    Existing rows for the account are only touched when they fall within the
    requested history window. Rows outside that window are left intact.

    Args:
        account_id: Account business identifier.
        user_id: Owner identifier associated with the account history rows.
        history: Daily balance entries (ISO date + numeric balance) to persist.
    """

    try:
        if not history:
            return

        now = datetime.now(timezone.utc)
        window_dates = [
            datetime.fromisoformat(record["date"]).date() for record in history
        ]
        window_start = min(window_dates)
        window_end = max(window_dates)

        existing_records = (
            AccountHistory.query.filter(AccountHistory.account_id == account_id)
            .filter(AccountHistory.date >= window_start)
            .filter(AccountHistory.date <= window_end)
            .all()
        )
        existing_by_date = {existing.date: existing for existing in existing_records}

        inserted_count = 0
        updated_count = 0
        for record, record_date in zip(history, window_dates):
            balance_value = Decimal(str(record["balance"])).quantize(TWOPLACES)
            existing_record = existing_by_date.get(record_date)

            if existing_record:
                existing_record.balance = balance_value
                existing_record.user_id = user_id
                existing_record.is_hidden = False
                existing_record.updated_at = now
                updated_count += 1
                continue

            history_record = AccountHistory(
                account_id=account_id,
                user_id=user_id,
                date=record_date,
                balance=balance_value,
                is_hidden=False,
                created_at=now,
                updated_at=now,
            )
            db.session.add(history_record)
            inserted_count += 1

        db.session.commit()

        print(
            "Cached balance history records for account "
            f"{account_id} ({inserted_count} inserted, {updated_count} updated)"
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
