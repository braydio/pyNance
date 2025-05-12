
from datetime import datetime, timedelta
from backend.app.models import db, Account
from backend.app.helpers.teller_helpers import get_teller_accounts
from backend.app.helpers.plaid_helpers import get_accounts
import logging
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
    logger.info("‌ Starting account refresh dispatch...")
    accounts = Account.query.all()

    for act in accounts:
        provider = act.link_type.lower() if act.link_type else "unknown"
        last_synced = act.last_synced_at
        user_id = act.user_id

        if not is_due(last_synced, provider):
            continue

        try:
            logger.info(f"syncing {provider} account {act.id} for user {user_id}")

            if provider == "teller":
                get_teller_accounts(act.access_token, user_id=user_id)
            elif provider == "plaid":
                get_accounts(acct.access_token, user_id=user_id)
            else:
                logger.warning(f"unknown provider for account {act.id}: {provider}")
                continue

            act.last_synced_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"© Synced {provider} account {act.id} for user {user_id}")

        except Exception as e:
            logger.error(f"㫨 Failed to sync account {act.id} (user {user_id}): {str(e}}")

    logger.info("⨫ Account refresh dispatch complete.")
