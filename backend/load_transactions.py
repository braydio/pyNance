"""Generate synthetic transactions for demo or testing accounts."""

import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from app import create_app, db
from app.models import Account, Category, Transaction

DAYS_PER_MONTH = 30
RANDOM_DAY_RANGE = (1, 28)
CATEGORY_PROBABILITY = 0.85
SPIKE_PROBABILITY = 0.1
SPIKE_MULTIPLIER_RANGE = (1.5, 2.0)

CATEGORIES: dict[str, tuple[int, int]] = {
    "groceries": (-80, -150),
    "rent": (-1000, -1600),
    "utilities": (-100, -250),
    "entertainment": (-50, -200),
    "subscriptions": (-10, -30),
    "salary": (2000, 4000),
}


def get_or_create_category(name: str) -> int:
    category = Category.query.filter_by(display_name=name).first()
    if not category:
        category = Category(display_name=name, primary_category=name)
        db.session.add(category)
        db.session.flush()
    return category.id


def generate_transactions_for_account(
    account: Account, months: int = 6, start_date: Optional[datetime] = None
) -> list[Transaction]:
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(
            days=DAYS_PER_MONTH * months
        )

    transactions = []
    for month_offset in range(months):
        month_date = start_date + timedelta(days=DAYS_PER_MONTH * month_offset)
        for category_name, amount_range in CATEGORIES.items():
            if random.random() < CATEGORY_PROBABILITY:
                variation = 1 + random.uniform(-0.15, 0.15)
                amount = round(random.uniform(*amount_range) * variation, 2)
                tx_date = month_date.replace(day=random.randint(*RANDOM_DAY_RANGE))

                category_id = get_or_create_category(category_name)

                transactions.append(
                    Transaction(
                        account_id=account.account_id,
                        user_id=account.user_id,
                        amount=amount,
                        category_id=category_id,
                        category=category_name,
                        date=tx_date,
                        description=f"Auto-{category_name.title()}",
                        provider="synthetic",
                        pending=False,
                    )
                )

            # Infrequent spikes
            if (
                category_name in ("utilities", "entertainment")
                and random.random() < SPIKE_PROBABILITY
            ):
                spike = round(
                    amount_range[1] * random.uniform(*SPIKE_MULTIPLIER_RANGE), 2
                )
                category_id = get_or_create_category(category_name)
                transactions.append(
                    Transaction(
                        account_id=account.account_id,
                        user_id=account.user_id,
                        amount=-spike,
                        category_id=category_id,
                        category=category_name,
                        date=month_date.replace(day=random.randint(*RANDOM_DAY_RANGE)),
                        description=f"Spike-{category_name.title()}",
                        provider="synthetic",
                        pending=False,
                    )
                )

    return transactions


def run(account_id: Optional[str] = None) -> None:
    app = create_app()
    with app.app_context():
        if account_id:
            accounts = Account.query.filter_by(account_id=account_id).all()
        else:
            accounts = Account.query.all()

        total = 0
        for acct in accounts:
            txs = generate_transactions_for_account(acct)
            db.session.add_all(txs)
            total += len(txs)

        db.session.commit()
        print(f"Generated {total} fake transactions across {len(accounts)} account(s).")


if __name__ == "__main__":
    run()  # optionally: run(account_id="abc123")
