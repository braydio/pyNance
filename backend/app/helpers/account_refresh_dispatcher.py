from datetime import datetime, timedelta

from app import create_app
from app.config import logger  # uses app logger
from app.helpers.plaid_helpers import get_accounts
from app.helpers.teller_helpers import get_teller_accounts
from app.models import Account, db

SYNC_INTERVALS = {
    "teller": timedelta(hours=8),
    "plaid": timedelta(days=2),
}


def is_due(last_synced, provider):
    """Returns True if the account should be refreshed."""
    if not last_synced:
        return True
    now = datetime.utcnow()
    return now - last_synced >= SYNC_INTERVALS.get(provider, timedelta(days=1))


def refresh_all_accounts():
    """
    Refreshes all linked accounts by provider type (Teller or Plaid),
    if they are due for sync based on SYNC_INTERVALS.
    Wraps execution in an application context.
    """
    app = create_app()
    with app.app_context():
        logger.info("🔁 Starting account refresh dispatcher...")

        accounts = Account.query.all()
        updated = 0
        skipped = 0

        for acct in accounts:
            provider = acct.link_type.lower() if acct.link_type else "unknown"
            last_synced = acct.last_refreshed
            user_id = acct.user_id

            if provider == "unknown":
                logger.warning(f"⚠️ Unknown provider for account {acct.id}")
                continue

            if not is_due(last_synced, provider):
                skipped += 1
                continue

            try:
                logger.info(
                    f"🔄 Syncing {provider} account {acct.id} for user {user_id}"
                )
                if provider == "teller":
                    get_teller_accounts(acct.access_token, user_id=user_id)
                elif provider == "plaid":
                    get_accounts(acct.access_token, user_id=user_id)
                else:
                    logger.warning(
                        f"⚠️ Unsupported provider for account {acct.id}: {provider}"
                    )
                    continue

                acct.last_refreshed = datetime.utcnow()
                db.session.commit()
                updated += 1
                logger.info(
                    f"✅ Synced {provider} account {acct.id} for user {user_id}"
                )

            except Exception as e:
                logger.error(
                    f"❌ Sync failed for account {acct.id}: {str(e)}", exc_info=True
                )

        logger.info(
            f"🔚 Account refresh complete: {updated} updated, {skipped} skipped."
        )
