# backend/app/sql/recurring_logic.py

from collections import defaultdict
from datetime import datetime

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
            diffs = [
                (dates[i] - dates[i-1]).days for i in range(1, len(dates))
            ]
            avg_days = sum(diffs) / len(diffs)
            if 28 <= avg_days <= 31:  # Roughly monthly
                recurring_items.append({
                    "merchant": merchant,
                    "amount": amount,
                    "frequency": "monthly",
                    "day": dates[-1].day
                })

    return recurring_items
