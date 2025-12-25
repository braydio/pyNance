"""Utility helpers for normalizing financial data."""

from decimal import Decimal

from app.config import logger
from app.models import Transaction
from flask import g, has_request_context

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Decimal | float | int | None) -> Decimal:
    """Return ``value`` as a ``Decimal`` rounded to two places."""

    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(TWOPLACES)
    return Decimal(str(value)).quantize(TWOPLACES)


def _normalize_cache():
    if has_request_context():
        return g.setdefault("normalize_cache", {})
    return None


def normalize_account_balance(balance, account_type, account_id=None):
    """Normalize the balance: liabilities are negative, assets are positive."""

    cache = _normalize_cache()
    key = None
    if cache is not None:
        key = (
            str(account_id) if account_id is not None else None,
            str(balance),
            str(account_type),
        )
        if key in cache:
            return cache[key]

    amount = _to_decimal(balance)
    if (account_type or "").lower() in [
        "credit card",
        "credit",
        "loan",
        "liability",
    ]:
        norm_balance = (-amount).quantize(TWOPLACES)
        logger.debug(
            "Normalized balance: type=%s value=%s",
            account_type,
            norm_balance,
        )
        result = norm_balance
    else:
        result = abs(amount).quantize(TWOPLACES)

    if cache is not None and key is not None:
        cache[key] = result
    return result


def normalize_transaction_amount(amount, account_type):
    """Return the transaction amount signed for display based on account type."""

    account_type = (account_type or "").lower()
    amt = _to_decimal(amount)

    if account_type in ["credit card", "credit", "loan", "liability"]:
        adjusted = (-amt).quantize(TWOPLACES)
        logger.debug(
            "Normalized transaction amount for credit account to %s",
            adjusted,
        )
        return adjusted

    logger.debug(
        "Preserving transaction amount %s for account type %s",
        amt,
        account_type,
    )
    return amt


def display_transaction_amount(txn: Transaction) -> float:
    """Return the signed amount for display."""

    amount = _to_decimal(txn.amount)

    raw_type = getattr(txn, "transaction_type", "") or ""
    txn_type = raw_type.lower()
    if txn_type == "expense":
        return float((-abs(amount)).quantize(TWOPLACES))
    if txn_type == "income":
        return float(abs(amount).quantize(TWOPLACES))

    return float((-amount).quantize(TWOPLACES))


def transform_transaction(txn: Transaction):
    """Transform raw transaction amount for display based on account type."""

    txn_type = txn.transaction_type or "expense"
    if txn.transaction_type:
        logger.debug("Transaction type as %s", txn_type)

    return normalize_transaction_amount(
        amount=txn.amount,
        account_type=txn.account.type if txn.account else None,
    )
