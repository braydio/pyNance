"""CLI entrypoint for running the scheduled account sync."""

import logging

from app.config import DIRECTORIES
from app.helpers.account_refresh_dispatcher import refresh_all_accounts

# Ensure log directory exists
log_path = DIRECTORIES["LOGS_DIR"] / "cron.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

# Configure logging to file
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


def main():
    """Trigger a refresh of all accounts for scheduled runs."""
    logging.info("🔄 Starting scheduled account sync...")
    try:
        refresh_all_accounts()
        logging.info("✅ Account sync completed successfully.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("❌ Sync failed: %s", e, exc_info=True)


if __name__ == "__main__":
    main()
