def normalize_amount(data):
    """
    Normalize a monetary amount to a float. Accepts strings (which may include currency symbols,
    thousands separators, or different decimal delimiters) and numeric types.

    Args:
        data (str, int, float): The input monetary amount.

    Returns:
        float: The normalized amount.

    Raises:
        ValueError: If the input cannot be parsed into a float.
    """
    if data is None:
        raise ValueError("Input data is None.")

    if isinstance(data, (int, float)):
        return float(data)

    # Convert to string and trim whitespace
    normalized = str(data).strip()

    # Remove common currency symbols
    for symbol in ("$", "€", "£"):
        normalized = normalized.replace(symbol, "")

    # Remove spaces that may be used as thousand separators
    normalized = normalized.replace(" ", "")

    # Determine if a comma is used as a decimal separator when no period exists
    if normalized.count(",") == 1 and normalized.count(".") == 0:
        normalized = normalized.replace(",", ".")
    else:
        # Otherwise, assume commas are thousand separators and remove them
        normalized = normalized.replace(",", "")

    try:
        return float(normalized)
    except ValueError as e:
        raise ValueError(f"Unable to normalize amount from input: {data}") from e
