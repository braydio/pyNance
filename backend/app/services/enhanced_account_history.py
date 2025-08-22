"""Enhanced account history service with caching and pre-computation.

This service provides optimized balance history computation with database caching
to improve performance for frequently requested account history data.
"""

from datetime import date, datetime, timedelta, timezone
from typing import List, Dict, Optional

from app.extensions import db
from app.models import Account, AccountHistory, Transaction
from app.services.account_history import compute_balance_history
from app.utils.finance_utils import normalize_account_balance
from sqlalchemy import func


def get_or_compute_account_history(
    account_id: str, 
    days: int = 30, 
    force_recompute: bool = False
) -> List[Dict[str, float]]:
    """
    Get account balance history, using cached data when possible.
    
    Args:
        account_id: The account identifier
        days: Number of days of history to return
        force_recompute: Whether to force recomputation even if cached data exists
        
    Returns:
        List of balance history records with date and balance fields
    """
    try:
        account = Account.query.filter_by(account_id=account_id).first()
        if not account:
            return []

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days - 1)
        
        # Check if we have recent cached data
        if not force_recompute:
            cached_history = get_cached_history(account_id, start_date, end_date)
            if cached_history:
                return cached_history
        
        # Compute fresh history
        current_balance = normalize_account_balance(account.balance, account.type)
        fresh_history = compute_fresh_history(
            account_id, current_balance, start_date, end_date
        )
        
        # Cache the results
        if fresh_history:
            cache_history(account_id, account.user_id, fresh_history)
        
        return fresh_history
        
    except Exception as e:
        print(f"Error in get_or_compute_account_history: {e}")
        return []


def get_cached_history(
    account_id: str, 
    start_date: date, 
    end_date: date
) -> Optional[List[Dict[str, float]]]:
    """
    Retrieve cached balance history from the database.
    
    Returns None if no suitable cached data is found.
    """
    try:
        # Query for cached history records
        cached_records = (
            AccountHistory.query
            .filter(AccountHistory.account_id == account_id)
            .filter(AccountHistory.date >= start_date)
            .filter(AccountHistory.date <= end_date)
            .order_by(AccountHistory.date.asc())
            .all()
        )
        
        # Check if we have complete coverage
        expected_days = (end_date - start_date).days + 1
        if len(cached_records) != expected_days:
            return None
            
        # Check if the most recent record is recent enough (within 1 day)
        latest_record = max(cached_records, key=lambda r: r.updated_at)
        if latest_record.updated_at < datetime.now(timezone.utc) - timedelta(days=1):
            return None
        
        # Convert to the expected format
        return [
            {
                "date": record.date.isoformat() if hasattr(record.date, 'isoformat') else str(record.date),
                "balance": round(float(record.balance or 0), 2)
            }
            for record in cached_records
        ]
        
    except Exception as e:
        print(f"Error retrieving cached history: {e}")
        return None


def compute_fresh_history(
    account_id: str,
    current_balance: float,
    start_date: date,
    end_date: date
) -> List[Dict[str, float]]:
    """
    Compute fresh balance history from transactions.
    """
    try:
        # Get aggregated transaction amounts by date
        tx_rows = (
            db.session.query(func.date(Transaction.date), func.sum(Transaction.amount))
            .filter(Transaction.account_id == account_id)
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .filter((Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None)))
            .group_by(func.date(Transaction.date))
            .all()
        )

        transactions = [
            {"date": row[0], "amount": float(row[1] or 0)} 
            for row in tx_rows
        ]
        
        return compute_balance_history(
            current_balance, transactions, start_date, end_date
        )
        
    except Exception as e:
        print(f"Error computing fresh history: {e}")
        return []


def cache_history(account_id: str, user_id: str, history: List[Dict[str, float]]):
    """
    Cache balance history in the database for future retrieval.
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Delete existing cached records for this account
        AccountHistory.query.filter(AccountHistory.account_id == account_id).delete()
        
        # Insert new records
        history_records = []
        for record in history:
            # Parse date string back to date object
            record_date = datetime.fromisoformat(record["date"]).date()
            
            history_record = AccountHistory(
                account_id=account_id,
                user_id=user_id,
                date=record_date,
                balance=record["balance"],
                is_hidden=False,  # We'll update this if needed
                created_at=now,
                updated_at=now
            )
            history_records.append(history_record)
        
        db.session.add_all(history_records)
        db.session.commit()
        
        print(f"Cached {len(history_records)} balance history records for account {account_id}")
        
    except Exception as e:
        print(f"Error caching history: {e}")
        db.session.rollback()


def update_account_balance_history(account_id: str, force_update: bool = False):
    """
    Update the cached balance history for an account.
    This should be called after account refresh operations.
    """
    try:
        # Force recomputation of history for common time ranges
        for days in [7, 30, 90, 365]:
            get_or_compute_account_history(
                account_id, days=days, force_recompute=True
            )
        
        print(f"Updated balance history cache for account {account_id}")
        
    except Exception as e:
        print(f"Error updating account balance history: {e}")
