from datetime import datetime, timedelta
from app.models import db, PlaidAccount, TellerAccount
from app.helpers.teller_helpers import get_teller_accounts
from app.helpers.plaid_helpers import get_accounts
from app.config import logger

SYNC_INTERVALS = {
    "teller": timedelta(hours=8),
    "plaid": timedelta(days=2)
}

def is_due(last_synced, provider):
    if not last_synced:
        return True
    now = datetime.utcnow()
    return now - last_synced >= SYNC_INTERVALS.get(provider, timedelta(days=1))

def refresh_all_accounts():
    logger.info("🏌 Starting account refresh dispatch...")

    # ---- Teller Accounts ----
    teller_accounts = TellerAccount.query.all()
    for act in teller_accounts:
        if not is_due(act.last_refreshed, "teller"):
            continue
        try:
            logger.info(f"syncing teller account {act.id} for user {act.user_id}")
            get_teller_accounts(act.access_token, user_id=act.user_id)
            act.last_refreshed = datetime.utcnow()
            db.session.commit()
            logger.info(f"⚤ Synced teller account {act.id} for user {act.user_id}")
        except Exception as e:
            logger.error(f"ë� Teller sync failed for account {act.id}: {str(e)}")

    # ---- Plaid Accounts ----
    plaid_accounts = PlaidAccount.query.all()
    for act in plaid_accounts:
        if not is_due(act.last_refreshed, "plaid"):
            continue
        try:
            logger.info(f"syncing plaid account {act.id} for user {act.user_id}")
            get_accounts(act.access_token, user_id=act.user_id)
            act.last_refreshed = datetime.utcnow()
            db.session.commit()
            logger.info(f"⚤ Synced plaid account {act.id} for user {act.user_id}")
        except Exception as e:
            logger.error(f"ë� Plaid sync failed for account {act.id}: {str(e}}")

    logger.info("⨫ Account refresh dispatch complete.")
