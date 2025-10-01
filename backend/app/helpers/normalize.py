"""Helpers for normalizing monetary amounts to ``Decimal`` values."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

TWOPLACES = Decimal("0.01")


def _to_decimal(value) -> Decimal:
    """Convert ``value`` to a ``Decimal`` rounded to two places."""

    if isinstance(value, Decimal):
        return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    try:
        return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Unable to convert {value!r} to Decimal") from exc


def normalize_amount(data):
    """Normalize a monetary amount to a ``Decimal``.

    Supports:
    - raw values (e.g. ``"$1,200.50"``, ``-100``, ``"1.000,50"``)
    - dicts like ``{"amount": 123.45, "transaction_type": "debit"}``

    Args:
        data (str | int | float | Decimal | dict): The input monetary amount or a dict.

    Returns:
        Decimal: Signed amount (negative for debits/liabilities, positive for credits/assets).

    Raises:
        ValueError: If the input is invalid or unrecognized.
    """

    if data is None:
        raise ValueError("Input data is None.")

    if isinstance(data, dict):
        amount = normalize_amount(data.get("amount"))
        ttype = data.get("transaction_type", "").lower()
        if ttype in ["debit", "liability", "credit card", "credit_card"]:
            return -abs(amount)
        if ttype in ["credit", "depository", "asset"]:
            return abs(amount)
        return amount  # fallback if unknown type

    if isinstance(data, (int, float, Decimal)):
        return _to_decimal(data)

    normalized = str(data).strip()

    for symbol in ("$", "€", "£"):
        normalized = normalized.replace(symbol, "")

    normalized = normalized.replace("\u00a0", "").replace(" ", "")

    if normalized.count(",") == 1 and normalized.count(".") == 0:
        normalized = normalized.replace(",", ".")
    else:
        normalized = normalized.replace(",", "")

    try:
        return _to_decimal(normalized)
    except ValueError as exc:
        raise ValueError(f"Unable to normalize amount from input: {data}") from exc
