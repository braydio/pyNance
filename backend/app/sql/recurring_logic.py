# backend/app/sql/recurring_logic.py

from collections import defaultdict
from datetime import datetime
from typing import Optional

from sqlalchemy import func

from app.extensions import db
from app.models import RecurringTransaction, Transaction
import uuid


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


def upsert_recurring(
    *,
    amount: float,
    description: str,
    frequency: str,
    next_due_date: datetime,
    confidence: Optional[float] = None,
):
    """Insert or update a RecurringTransaction linked to a matching Transaction."""

    tx = (
        db.session.query(Transaction)
        .filter(func.lower(Transaction.description) == description.lower())
        .filter(Transaction.amount == amount)
        .order_by(Transaction.date.desc())
        .first()
    )

    if not tx:
        tx = Transaction(
            transaction_id=str(uuid.uuid4())[:12],
            amount=amount,
            date=datetime.utcnow(),
            description=description,
            provider="detected",
        )
        db.session.add(tx)
        db.session.flush()

    rec = RecurringTransaction.query.filter_by(transaction_id=tx.transaction_id).first()

    status = "updated" if rec else "inserted"
    if rec:
        rec.frequency = frequency
        rec.next_due_date = next_due_date
        rec.notes = f"confidence:{confidence}" if confidence is not None else None
    else:
        rec = RecurringTransaction(
            transaction_id=tx.transaction_id,
            frequency=frequency,
            next_due_date=next_due_date,
            notes=f"confidence:{confidence}" if confidence is not None else None,
        )
        db.session.add(rec)

    db.session.commit()
    return {"status": status, "recurring_id": rec.id}
