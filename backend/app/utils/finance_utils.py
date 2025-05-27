# ap/utils/finance_utils.py
def normalize_balance(balance, account_type):
    """
    Adjust balance based on account type.
    Liabilities (e.g. credit, loan) should be negative.
    """
    if account_type.lower() in ["credit", "loan", "liability"]:
        return -abs(balance)
    return abs(balance)


def normalize_transaction_amount(amount, account_type):
    """
    Normalize transaction amount for display and balance computation.
    For liabilities, transactions increase negative balance.
    """
    if account_type.lower() in ["credit", "loan", "liability"]:
        return -abs(amount)  # Charges on liability increase its debt
    return abs(amount)  # Expenses decrease assets
