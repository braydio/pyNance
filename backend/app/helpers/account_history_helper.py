from datetime import datetime
from collections import defaultdict

from app.extensions import db
from app.models import Transaction, AccountHistory


def update_account_history():
    """
    Aggregate daily transaction totals into AccountHistory entries per account.
    This is used as the backend data source for forecasting.
    """
    print("🔁 Starting account history aggregation...")

    # Daily sum per account_id → {account_id: {date: balance}}
    daily_balances = defaultdict(lambda: defaultdict(float))
    transactions = Transaction.query.all()

    for tx in transactions:
        tx_date = tx.date.date() if hasattr(tx.date, "date") else tx.date
        daily_balances[tx.account_id][tx_date] += tx.amount

    records = []
    for account_id, dated in daily_balances.items():
        for tx_date, total in dated.items():
            records.append(
                AccountHistory(account_id=account_id, date=tx_date, balance=total)
            )

    db.session.bulk_save_objects(records)
    db.session.commit()

    print(f"✅ AccountHistory updated with {len(records)} records.")
