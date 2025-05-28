# ap/utils/finance_utils.py
def normalize_account_balance(balance, account_type):
    """
    Normalize the balance: liabilities are negative, assets are positive.
    """
    if account_type.lower() in ["credit", "loan", "liability"]:
        return -abs(balance)
    return abs(balance)


def normalize_transaction_amount(amount, account_type, transaction_type="expense"):
    account_type = (account_type or "").lower()
    transaction_type = (transaction_type or "").lower()
    amount = abs(amount)

    if transaction_type == "expense":
        return -amount
    elif transaction_type in ["income", "payment"]:
        return amount
    return amount


def display_transaction_amount(txn: Transaction) -> float:
    """Transform raw transaction amount for display based on account type."""
    from app.models import Account  # if needed

    return normalize_transaction_amount(
        amount=txn.amount,
        account_type=txn.account.type if txn.account else None,
        transaction_type=txn.transaction_type or "expense",
    )
