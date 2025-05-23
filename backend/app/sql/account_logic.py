#upsert_accounts update block fix
from datetime import datetime

today = datetime.utcnow().date()

existing_history = AccountHistory.query.filter_by(account_id=account_id, date=today).first()
if existing_history:
    logger.debug(f"[UPDATING] AccountHistory for account_id={account_id} on date={today}"))
    existing_history.balance = balance
    existing_history.updated_at = datetime.utcnow()
    logger.debug(f"History record already exists for account {account.account_id} for date {today}.")
else:
    logger.debug(f"[CREATING] New AccountHistory for account_id={account_id} on date={today}")
    new_history = AccountHistory(
        account_id=account_id,
        user_id=user_id,
        date=today,
        balance=balance,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(new_history)