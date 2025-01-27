from datetime import datetime


def format_transactions_for_display(transactions):
    """Format transaction data for compact display in the frontend."""
    formatted_transactions = []
    for transaction in transactions:
        formatted_transactions.append(
            {
                "transaction_id": transaction["transaction_id"],
                "date": datetime.strptime(transaction["date"], "%Y-%m-%d").strftime(
                    "%m/%d/%Y"
                ),  # Short date format
                "name": transaction["name"],
                "amount": f"({abs(transaction['amount']):,.2f})"
                if transaction["amount"] < 0
                else f"{transaction['amount']:,.2f}",  # Accounting style
                "category": transaction["category"],
                "merchant_name": transaction.get(
                    "merchant_name", "N/A"
                ),  # Default to N/A if missing
                "institution_name": transaction.get("institution_name", "Unknown"),
                "account_name": transaction.get("account_name", "Unknown Account"),
                "account_type": transaction.get("account_type", "Unknown"),
                "account_subtype": transaction.get("account_subtype", "Unknown"),
            }
        )
    return formatted_transactions
