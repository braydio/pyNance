
from datetime import datetime, timedelta
from backend.app.models import db, Account
from backend.app.helpers.teller_helpers import get_teller_accounts
from backend.app.helpers.plaid_helpers import get_accounts
import logging

logger = logging.getLogger(__name__)

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
    logger.info("Starting account refresh dispatch...")
    accounts = Account.query.all()

    for acct in accounts:
        provider = acct.provider.lower() if acct.provider else "unknown"
        last_synced = acct.last_synced_at
        user_id = acct.user_id

        if not is_due(last_synced, provider):
            continue

        try:
            logger.info(f"Syncing {provider} account {acct.id} for user {user_id}")
            if provider == "teller":
                get_teller_accounts(acct.access_token, user_id=user_id)
            elif provider == "plaid":
                get_accounts(acct.access_token, user_id=user_id)
            else:
                logger.warning(f"Unknown provider for account {act.id}: {provider}")
                continue

            act.last_synced_at = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            logger.error(fBFailed to sync account {acct.id}: {str(e)}")

    logger.info("Account refresh dispatch complete.")
