def normalize_account_balance(balance, account_type):
    """
    Normalize the balance: liabilities are negative, assets are positive.
    """
    if account_type.lower() in ["credit", "loan", "liability"]:
        return -abs(balance)
    return abs(balance)
