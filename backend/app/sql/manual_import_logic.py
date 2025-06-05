# manual_import_logic.py
from datetime import datetime

from app.extensions import db
from app.models import Transaction


def upsert_imported_transactions(transactions, user_id=None, account_id=None):
    """
    Inserts imported transactions (parsed from CSV or PDF).
    Optional user_id/account_id can be added if relevant.
    """
    inserted = 0

    for tx in transactions:
        # Safely parse the transaction date if provided
        raw_date = tx.get("date")
        if raw_date:
            try:
                parsed_date = datetime.fromisoformat(raw_date)
            except (TypeError, ValueError):
                parsed_date = datetime.utcnow()
        else:
            parsed_date = datetime.utcnow()

        txn = Transaction(
            transaction_id=tx.get("transaction_id"),
            account_id=account_id,
            user_id=user_id,
            amount=tx.get("amount", 0),
            date=parsed_date,
            description=tx.get("name"),
            category=tx.get("type"),
            provider=tx.get("provider", "manual"),
            pending=False,
        )
        db.session.add(txn)
        inserted += 1

    db.session.commit()
    return inserted
