# backend/app/sql/recurring_logic.py

from collections import defaultdict
from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models import RecurringTransaction, Transaction


def find_recurring_items(transactions):
    """
    Detect recurring monthly transactions based on merchant name and date patterns.
    Returns a list of dicts with estimated frequency and next date.
    """
    grouped = defaultdict(list)

    for tx in transactions:
        merchant = tx.get("merchant_name") or tx.get("description") or "Unknown"
        amount = round(float(tx.get("amount", 0.0)), 2)
        date_str = tx.get("date")
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue

        key = (merchant.lower(), amount)
        grouped[key].append(date)

    recurring_items = []
    for (merchant, amount), dates in grouped.items():
        if len(dates) >= 2:
            dates.sort()
            diffs = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
            avg_days = sum(diffs) / len(diffs)
            if 28 <= avg_days <= 31:  # Roughly monthly
                recurring_items.append(
                    {
                        "merchant": merchant,
                        "amount": amount,
                        "frequency": "monthly",
                        "day": dates[-1].day,
                    }
                )

    return recurring_items


def upsert_recurring(amount, description, frequency, next_due_date, confidence=1):
    """Insert or update a RecurringTransaction record.

    Args:
        amount (float): Transaction amount used to locate a matching transaction.
        description (str): Transaction description signature.
        frequency (str): Detected frequency string.
        next_due_date (date): When the next instance is expected.
        confidence (int): Optional indicator of match strength.

    Returns:
        dict: Result summary including created/updated status.
    """

    tx = (
        Transaction.query.filter(
            func.lower(Transaction.description) == description.lower()
        )
        .filter(Transaction.amount == amount)
        .order_by(Transaction.date.desc())
        .first()
    )

    if not tx:
        return {"status": "no_match"}

    existing = RecurringTransaction.query.filter_by(
        transaction_id=tx.transaction_id
    ).first()

    if existing:
        existing.frequency = frequency
        existing.next_due_date = next_due_date
        existing.notes = f"confidence:{confidence}"
        db.session.commit()
        return {"status": "updated", "id": existing.id}

    rec = RecurringTransaction(
        transaction_id=tx.transaction_id,
        frequency=frequency,
        next_due_date=next_due_date,
        notes=f"confidence:{confidence}",
    )
    db.session.add(rec)
    db.session.commit()
    return {"status": "inserted", "id": rec.id}
