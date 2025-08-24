"""Utilities for refreshing external accounts on a schedule."""

from datetime import date, datetime, timedelta, timezone

from app.config import logger  # uses app logger
from app.models import Account, db
from app.services import sync_service

SYNC_INTERVALS = {
    "teller": timedelta(hours=8),
    "plaid": timedelta(days=2),
}


def is_due(last_synced, provider):
    """Return ``True`` if the account should be refreshed.

    Args:
        last_synced: The last refresh timestamp as ``datetime`` or ``date``.
        provider: Provider name to determine refresh interval.
    """
    if not last_synced:
        return True

    now = datetime.now(timezone.utc)
    if isinstance(last_synced, date) and not isinstance(last_synced, datetime):
        last_synced = datetime.combine(last_synced, datetime.min.time(), timezone.utc)
    elif isinstance(last_synced, datetime) and last_synced.tzinfo is None:
        last_synced = last_synced.replace(tzinfo=timezone.utc)

    return now - last_synced >= SYNC_INTERVALS.get(provider, timedelta(days=1))


def refresh_all_accounts():
    """
    Refreshes all linked accounts by provider type (Teller or Plaid)
    if they are due for sync based on ``SYNC_INTERVALS``.
    Requires that the caller already created a Flask ``app_context``.
    """
    logger.info("🔁 Starting account refresh dispatcher...")

    accounts = Account.query.all()
    updated = 0
    skipped = 0

    for acct in accounts:
        provider = acct.link_type.lower() if acct.link_type else "unknown"

        if provider == "teller":
            rel = acct.teller_account
        elif provider == "plaid":
            rel = acct.plaid_account
        else:
            logger.warning(f"⚠️ Unknown provider for account {acct.id}")
            continue

        last_synced = getattr(rel, "last_refreshed", None)

        if not is_due(last_synced, provider):
            skipped += 1
            continue

        try:
            logger.info(
                f"🔄 Syncing {provider} account {acct.id} for user {acct.user_id}"
            )
            sync_service.sync_account(acct)
            if rel:
                rel.last_refreshed = datetime.now(timezone.utc)
            db.session.commit()
            updated += 1
            logger.info(
                f"✅ Synced {provider} account {acct.id} for user {acct.user_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ Sync failed for account {acct.id}: {str(e)}", exc_info=True
            )

    logger.info(f"🔚 Account refresh complete: {updated} updated, {skipped} skipped.")
