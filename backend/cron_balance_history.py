"""CLI entrypoint for running scheduled balance history updates."""

from app import create_app
from app.config import logger
from app.services.balance_history import update_all_accounts_balance_history


def main():
    """Trigger balance history refresh for all accounts."""
    logger.info("[CRON] 🧮 Starting scheduled balance history update...")
    app = create_app()
    with app.app_context():
        try:
            update_all_accounts_balance_history(days=365, force_update=False)
            logger.info("[CRON] ✅ Balance history update completed successfully.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "[CRON] ❌ Balance history update failed: %s", e, exc_info=True
            )


if __name__ == "__main__":
    main()
