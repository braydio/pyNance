def deduplicate_transactions(transactions, amount_epsilon=0.01, date_epsilon=1):
    seen = set()
    deduped = []
    for i, txn in enumerate(transactions):
        if txn.transaction_id in seen:
            continue
        # Compare to the rest of the transactions
        is_duplicate = False
        for other in transactions[i + 1 :]:
            if other.transaction_id in seen:
                continue
            if (
                abs(txn.amount - other.amount) <= amount_epsilon
                and abs((txn.date - other.date).days) <= date_epsilon
                and txn.description == other.description
            ):
                # Mark one as duplicate (keep txn, skip other)
                seen.add(other.transaction_id)
                is_duplicate = True
        deduped.append(txn)
    return deduped
