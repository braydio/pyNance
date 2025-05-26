def normalize_amount(data):
    """
    Normalize a monetary amount to a float. Supports:
    - raw values (e.g. "$1,200.50", -100, "1.000,50")
    - dicts like {"amount": 123.45, "transaction_type": "debit"}

    Args:
        data (str | int | float | dict): The input monetary amount or a dict.

    Returns:
        float: Signed amount (negative for debits/liabilities, positive for credits/assets).

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
        elif ttype in ["credit", "depository", "asset"]:
            return abs(amount)
        return amount  # fallback if unknown type

    if isinstance(data, (int, float)):
        return float(data)

    normalized = str(data).strip()

    for symbol in ("$", "€", "£"):
        normalized = normalized.replace(symbol, "")

    normalized = normalized.replace("\u00a0", "").replace(" ", "")

    if normalized.count(",") == 1 and normalized.count(".") == 0:
        normalized = normalized.replace(",", ".")
    else:
        normalized = normalized.replace(",", "")

    try:
        return float(normalized)
    except ValueError as e:
        raise ValueError(f"Unable to normalize amount from input: {data}") from e
