# manual_import_logic.py
from app.extensions import db
from app.models import Transaction


def upsert_imported_transactions(transactions, user_id=None, account_id=None):
    """
    Inserts imported transactions (parsed from CSV or PDF).
    Optional user_id/account_id can be added if relevant.
    """
    inserted = 0

    for tx in transactions:
        txn = Transaction(
            transaction_id=tx.get("transaction_id"),
            name=tx.get("name"),
            date=tx.get("date"),
            amount=tx.get("amount"),
            type=tx.get("type"),
            provider=tx.get("provider", "manual"),
            currency=tx.get("currency", "USD"),
            user_id=user_id,  # Assuming the model has this field
            account_id=account_id,  # Assuming the model has this field
        )
        db.session.add(txn)
        inserted += 1

    db.session.commit()
    return inserted
