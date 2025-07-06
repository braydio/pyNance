# backend/scripts/cron_sync.py

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
    logging.info("🔄 Starting scheduled account sync...")
    try:
        refresh_all_accounts()
        logging.info("✅ Account sync completed successfully.")
    except Exception as e:
        logging.error(f"❌ Sync failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
