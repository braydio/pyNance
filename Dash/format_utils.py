def format_transactions_for_display(transactions):
    """Format transaction data for compact display in the frontend."""
    formatted_transactions = []
    for transaction in transactions:
        formatted_transactions.append(
            {
                "transaction_id": transaction["transaction_id"],
                "date": transaction["date"],  # Short date format
                "name": transaction["name"],
                "amount": transaction["amount"],
                "category": transaction.get("category", ["Uncategorized"])[-1],
                "merchant_name": transaction.get("merchant_name", "Unknown"),
                "institution_name": transaction.get("institution_name", "Unknown"),
                "account_name": transaction.get("account_name", "Unknown Account"),
                "account_type": transaction.get("account_type", "Unknown"),
                "account_subtype": transaction.get("account_subtype", "Unknown"),
            }
        )
    return formatted_transactions
