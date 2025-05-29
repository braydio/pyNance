from app.config import logger


def normalize_account_balance(balance, account_type):
    """
    Normalize the balance: liabilities are negative, assets are positive.
    """
    logger.debug(
        "This module at backend/app/utils/normalization.py is being deprecated."
    )
    logger.debug("Please update this routing and remove the module.")
    if account_type.lower() in ["credit", "loan", "liability"]:
        return -abs(balance)
    return abs(balance)
