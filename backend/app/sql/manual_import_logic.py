# manual_import_logic.py
from datetime import datetime, timezone

from app.extensions import db
from app.models import Transaction
from app.sql import transaction_rules_logic


def upsert_imported_transactions(transactions, user_id=None, account_id=None):
    """
    Inserts imported transactions (parsed from CSV or PDF).
    Optional user_id/account_id can be added if relevant.
    """
    inserted = 0

    for tx in transactions:
        tx = transaction_rules_logic.apply_rules(user_id, dict(tx))
        # Safely parse the transaction date if provided
        raw_date = tx.get("date")
        if raw_date:
            try:
                parsed_date = datetime.fromisoformat(raw_date)
            except (TypeError, ValueError):
                parsed_date = datetime.now(timezone.utc)
        else:
            parsed_date = datetime.now(timezone.utc)

        txn = Transaction(
            transaction_id=tx.get("transaction_id"),
            account_id=account_id,
            user_id=user_id,
            amount=tx.get("amount", 0),
            date=parsed_date,
            description=tx.get("name"),
            category=tx.get("category"),
            category_id=tx.get("category_id"),
            merchant_name=tx.get("merchant_name"),
            provider=tx.get("provider", "manual"),
            pending=False,
            updated_by_rule=tx.get("updated_by_rule", False),
        )
        db.session.add(txn)
        inserted += 1

    db.session.commit()
    return inserted
