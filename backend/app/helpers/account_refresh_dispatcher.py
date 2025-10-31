"""Utilities for refreshing external accounts on a schedule."""

from datetime import date, datetime, timedelta, timezone

from app.config import logger  # uses app logger
from app.models import Account, db
from app.services import sync_service

SYNC_INTERVALS = {
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
    """Refresh Plaid-linked accounts that are due for sync.

    The caller must ensure a Flask ``app_context`` is active so database updates
    persist. Accounts that are not Plaid-linked are skipped with a warning.
    """
    logger.info("🔁 Starting account refresh dispatcher...")

    accounts = Account.query.all()
    updated = 0
    skipped = 0

    for acct in accounts:
        provider = acct.link_type.lower() if acct.link_type else "unknown"

        if provider == "plaid":
            rel = acct.plaid_account
        else:
            logger.warning("⚠️ Unknown provider for account %s", acct.id)
            skipped += 1
            continue

        last_synced = getattr(rel, "last_refreshed", None)

        if not is_due(last_synced, provider):
            skipped += 1
            continue

        try:
            logger.info(
                "🔄 Syncing %s account %s for user %s",
                provider,
                acct.id,
                acct.user_id,
            )
            sync_service.sync_account(acct)
            if rel:
                rel.last_refreshed = datetime.now(timezone.utc)
            db.session.commit()
            updated += 1
            logger.info(
                "✅ Synced %s account %s for user %s",
                provider,
                acct.id,
                acct.user_id,
            )

        except Exception as e:
            logger.error(
                "❌ Sync failed for account %s: %s",
                acct.id,
                str(e),
                exc_info=True,
            )

    logger.info(
        "🔚 Account refresh complete: %d updated, %d skipped.", updated, skipped
    )
