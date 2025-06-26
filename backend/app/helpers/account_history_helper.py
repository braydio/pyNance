"""Helper for aggregating daily account balances."""

from app.config import logger
from app.extensions import db
from app.models import AccountHistory, Transaction
from sqlalchemy import func


def update_account_history():
    """Aggregate transactions into daily ``AccountHistory`` records."""
    logger.info("🔁 Starting account history aggregation...")

    grouped = (
        db.session.query(
            Transaction.account_id,
            func.date(Transaction.date).label("tx_date"),
            func.sum(Transaction.amount).label("balance"),
        )
        .group_by(Transaction.account_id, func.date(Transaction.date))
        .all()
    )

    records = [
        AccountHistory(account_id=acc_id, date=tx_date, balance=bal)
        for acc_id, tx_date, bal in grouped
    ]

    db.session.bulk_save_objects(records)
    db.session.commit()

    logger.info(f"✅ AccountHistory updated with {len(records)} records.")
