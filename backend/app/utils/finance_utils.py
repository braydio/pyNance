"""Utility helpers for normalizing financial data."""

from app.config import logger
from app.models import Transaction


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
    """Return the transaction amount signed for display based on account type."""
    account_type = (account_type or "").lower()
    amt = float(amount)

    # Liability/credit accounts report positive amounts for charges and negative
    # amounts for payments. For a net-worth view we flip the sign so that
    # charges appear negative and payments appear positive.
    if account_type in ["credit card", "credit", "loan", "liability"]:
        adjusted = -amt
        logger.info(f"Normalized transaction amount for credit account to {adjusted}")
        return adjusted

    # For asset/depository accounts we keep the provider's sign intact.
    logger.info(f"Preserving transaction amount {amt} for account type {account_type}")
    return amt


def display_transaction_amount(txn: Transaction) -> float:
    """Return the signed amount for display.

    Blade reports expenses as positive values and income as negative values. For
    a more intuitive UI, expenses should appear negative and income positive.
    If ``transaction_type`` is available it will be honored, otherwise the sign
    of ``txn.amount`` is used to infer the type.
    """

    amount = float(txn.amount)

    raw_type = getattr(txn, "transaction_type", "") or ""
    txn_type = raw_type.lower()
    if txn_type == "expense":
        return -abs(amount)
    if txn_type == "income":
        return abs(amount)

    # Fallback: infer from stored sign (Blade uses positive for expenses)
    return -amount


def transform_transaction(txn: Transaction):
    """Transform raw transaction amount for display based on account type."""
    txn_type = txn.transaction_type or "expense"
    if txn.transaction_type:
        logger.debug(f"Transaction type as {txn_type}")

    return normalize_transaction_amount(
        amount=txn.amount,
        account_type=txn.account.type if txn.account else None,
    )
