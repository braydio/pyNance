"""CLI entrypoint for running the scheduled account sync."""

from app.config import logger
from app.helpers.account_refresh_dispatcher import refresh_all_accounts


def main():
    """Trigger a refresh of all accounts for scheduled runs."""
    logger.info("[CRON] 🔄 Starting scheduled account sync...")
    try:
        refresh_all_accounts()
        logger.info("[CRON] ✅ Account sync completed successfully.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("[CRON] ❌ Sync failed: %s", e, exc_info=True)


if __name__ == "__main__":
    main()
