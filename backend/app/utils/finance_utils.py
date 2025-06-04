# app/utils/finance_utils.py
from app.models import Transaction
from app.config import logger


def normalize_account_balance(balance, account_type):
    """
    Normalize the balance: liabilities are negative, assets are positive.
    """
    if account_type.lower() in ["credit card", "credit", "loan", "liability"]:
        norm_balance = -1 * (balance)
        logger.info(
            f"Account type {account_type} - balance normalized to {norm_balance}"
        )
        return norm_balance
    return abs(balance)


def normalize_transaction_amount(amount, account_type):
    account_type = (account_type or "").lower()
    amount = abs(amount)

    if account_type.lower() in ["credit card", "credit", "loan", "liability"]:
        normalized_amount = -1 * (amount)
        logger.info(f"Normalized transaction amount to {normalized_amount}")
        return normalized_amount
    else:
        logger.info(f"Cannot determine for {account_type}, returning {amount}")
        return amount


def display_transaction_amount(txn: Transaction) -> float:
    """
    Returns a formatted version of the transaction amount for display purposes.

    This function converts the transaction’s amount into a float and then applies a sign
    convention based on the transaction type. It assumes that the Transaction object has
    an 'amount' attribute (which can be converted to float) and a 'transaction_type' attribute,
    where 'expense' transactions are displayed as negative (money out) and any other type
    (e.g. income) is displayed as a positive amount.

    Args:
        txn (Transaction): The transaction instance containing financial data.

    Returns:
        float: The properly signed amount for display.
    """
    # Convert the raw amount to a float.
    amount = float(txn.amount)

    # If the transaction is an expense, return the negative absolute value.
    if getattr(txn, "transaction_type", "").lower() == "expense":
        return -abs(amount)

    # Otherwise, return the absolute value (assuming income or similar).
    return abs(amount)


def transform_transaction(txn: Transaction):
    """Transform raw transaction amount for display based on account type."""
    type = txn.transaction_type
    if type:
        print(f"Transaction type as {type}")
        transaction_type = type
    else:
        transaction_type = "expense"

    return normalize_transaction_amount(
        amount=txn.amount,
        account_type=txn.account.type if txn.account else None,
    )
