"""
Background tasks for maintaining balance history.

This module provides functions that can be run as background jobs
to keep the account_history table up-to-date.
"""

from app.config import logger
from app.services.balance_history import update_all_accounts_balance_history


def update_all_balance_history():
    """
    Background task to update balance history for all accounts.

    This can be called by a scheduler or triggered after bulk
    transaction updates.
    """
    logger.info("Starting background task: update all balance history")

    try:
        results = update_all_accounts_balance_history(days=90)

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        logger.info(
            "Balance history update completed: %d/%d accounts updated successfully",
            successful,
            total,
        )

        if successful < total:
            failed_accounts = [
                acc_id for acc_id, success in results.items() if not success
            ]
            logger.warning(
                "Failed to update balance history for accounts: %s",
                failed_accounts,
            )

        return results

    except Exception as e:
        logger.error("Error in background balance history update: %s", e, exc_info=True)
        return {}


def update_single_account_balance_history(account_id: str):
    """
    Background task to update balance history for a single account.

    Args:
        account_id: The account to update

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(
        "Starting background task: update balance history for %s", account_id
    )

    try:
        from app.services.balance_history import update_account_balance_history

        success = update_account_balance_history(account_id, days=90, force_update=True)

        if success:
            logger.info(
                "Successfully updated balance history for %s", account_id
            )
        else:
            logger.warning("Failed to update balance history for %s", account_id)

        return success

    except Exception as e:
        logger.error(
            "Error updating balance history for %s: %s", account_id, e, exc_info=True
        )
        return False
