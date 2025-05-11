from datetime import datetime, timedelta
from backend.app.models import db, Account
from backend.app.helpers.teller_sync import sync_teller_account
from backend.app.helpers.plaid_sync import sync_plaid_account
import logging

logger = logging.getLogger(__name__)

SYNC_INTERVALS = {
    "teller": timedelta(hours=8),    # 3x/day
    "plaid": timedelta(days=2)       # 3x/week
}

def is_due(last_synced, provider):
    if not last_synced:
        return True
    now = datetime.utcnow()
    return now - last_synced >= SYNC_INTERVALS.get(provider, timedelta(days=1))

def refresh_all_accounts():
    logger.info("Starting account refresh dispatch...")
    accounts = Account.query.all()

    synced_count = 0
    skipped_count = 0

    for acct in accounts:
        provider = acct.provider.lower() if acct.provider else "unknown"
        last_synced = acct.last_synced_at
        user_id = acct.user_id

        if not is_due(last_synced, provider):
            skipped_count += 1
            continue

        try:
            if provider == "teller":
                logger.info(f"Syncing Teller account {acct.id}")
                sync_teller_account(acct, user_id=user_id)
            elif provider == "plaid":
                logger.info(f"Syncing Plaid account {acct.id}")
                sync_plaid_account(acct, user_id=user_id)
            else:
                logger.warning(f"Unknown provider for account {acct.id}: {provider}")
                continue

            acct.last_synced_at = datetime.utcnow()
            db.session.commit()
            synced_count += 1

        except Exception as e:
            logger.error(f"Failed to sync account {acct.id}: {str(e)}")

    logger.info(f"Account refresh dispatch complete. Synced: {synced_count}, Skipped: {skipped_count}")

