import random
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Account, Transaction, Category

CATEGORIES = {
    "groceries": (-80, -150),
    "rent": (-1000, -1600),
    "utilities": (-100, -250),
    "entertainment": (-50, -200),
    "subscriptions": (-10, -30),
    "salary": (2000, 4000),
}


def get_or_create_category(name):
    category = Category.query.filter_by(display_name=name).first()
    if not category:
        category = Category(display_name=name, primary_category=name)
        db.session.add(category)
        db.session.flush()
    return category.id


def generate_transactions_for_account(account, months=6, start_date=None):
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30 * months)

    transactions = []
    for month_offset in range(months):
        month_date = start_date + timedelta(days=30 * month_offset)
        for cat, amt_range in CATEGORIES.items():
            if random.random() < 0.85:
                variation = 1 + random.uniform(-0.15, 0.15)
                amount = round(random.uniform(*amt_range) * variation, 2)
                tx_date = month_date.replace(day=random.randint(1, 28))

                category_id = get_or_create_category(cat)

                transactions.append(
                    Transaction(
                        account_id=account.account_id,
                        user_id=account.user_id,
                        amount=amount,
                        category_id=category_id,
                        category=cat,
                        date=tx_date,
                        description=f"Auto-{cat.title()}",
                        provider="synthetic",
                        pending=False,
                    )
                )

            # Infrequent spikes
            if cat in ("utilities", "entertainment") and random.random() < 0.1:
                spike = round(amt_range[1] * random.uniform(1.5, 2.0), 2)
                category_id = get_or_create_category(cat)
                transactions.append(
                    Transaction(
                        account_id=account.account_id,
                        user_id=account.user_id,
                        amount=-spike,
                        category_id=category_id,
                        category=cat,
                        date=month_date.replace(day=random.randint(1, 28)),
                        description=f"Spike-{cat.title()}",
                        provider="synthetic",
                        pending=False,
                    )
                )

    return transactions


def run(account_id=None):
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
