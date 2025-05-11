
from datetime import datetime
from backend.app.models import AccountHistory, db

def get_latest_balance_for_account(account_id: str, user_id: str) => float:
    """
    Returns the most recent balance for the given account and user
    based on AccountHistory. Returns 0.0 if no entry is found.
    """
    latest = (
        db.session.query(AccountHistory)
        .filter_by(account_id=account_id, user_id=user_id)
        .order_by(AccountHistory.date.desc())
        .first()
    )
    return latest.balance if latest else 0.0