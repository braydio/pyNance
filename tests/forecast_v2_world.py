"""Seeded SQLite world shared by the Forecast V2 service and API tests."""

import random
from datetime import date, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Account, AccountHistory, Transaction

AS_OF = date(2026, 10, 31)
START = date(2026, 11, 1)


def seed_world():
    """Alice: two cash accounts, a card, an investment account; Bob: one unrelated account."""
    for account_id, user, acct_type, subtype in (
        ("chk", "alice", "depository", "checking"),
        ("sav", "alice", "depository", "savings"),
        ("card", "alice", "credit", "credit card"),
        ("brk", "alice", "investment", "brokerage"),
        ("bob-chk", "bob", "depository", "checking"),
    ):
        db.session.add(Account(account_id=account_id, user_id=user, name=account_id, type=acct_type, subtype=subtype))
    db.session.flush()
    for account_id, user, balance in (
        ("chk", "alice", "4000.00"),
        ("sav", "alice", "1000.00"),
        ("card", "alice", "700.00"),
        ("brk", "alice", "5000.00"),
        ("bob-chk", "bob", "777.00"),
    ):
        for offset in (0, 1, 2):
            db.session.add(
                AccountHistory(
                    account_id=account_id, user_id=user, date=AS_OF - timedelta(days=offset), balance=Decimal(balance)
                )
            )
    rng = random.Random(11)
    n = 0

    def add(day, account, amount, name, user="alice", **extra):
        nonlocal n
        n += 1
        db.session.add(
            Transaction(
                transaction_id=f"w{n:05d}",
                user_id=user,
                account_id=account,
                date=day,
                amount=Decimal(str(amount)),
                description=name,
                **extra,
            )
        )

    for offset in range(120):
        day = AS_OF - timedelta(days=offset)
        if (day - date(2026, 7, 10)).days % 14 == 0 and day >= date(2026, 7, 10):
            add(day, "chk", 2000, "ACME PAYROLL")
        if day.day == 1:
            add(day, "chk", -1500, "LANDLORD PROPERTIES")
        if rng.random() < 0.65:
            add(day, "chk", -rng.choice([12, 18, 27, 44, 63, 80]), f"Shop{chr(65 + offset % 26)}")
        if rng.random() < 0.25:
            add(day, "card", -rng.choice([15, 35, 90]), f"Online{chr(65 + offset % 26)}")
    db.session.add(
        Transaction(
            transaction_id="pay-out",
            user_id="alice",
            account_id="chk",
            date=AS_OF - timedelta(days=9),
            amount=Decimal("-300.00"),
            description="Card payment",
            is_internal=True,
            internal_match_id="pay-in",
        )
    )
    db.session.add(
        Transaction(
            transaction_id="pay-in",
            user_id="alice",
            account_id="card",
            date=AS_OF - timedelta(days=9),
            amount=Decimal("300.00"),
            description="Payment received",
            is_internal=True,
            internal_match_id="pay-out",
        )
    )
    add(AS_OF - timedelta(days=3), "bob-chk", -4000, "Bob's big purchase", user="bob")
    db.session.commit()
