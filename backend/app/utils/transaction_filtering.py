# backend/app/utils/transaction_filtering.py



def collapse_internal_transfers(transactions, date_epsilon=1, amount_epsilon=0.01):
    seen = set()
    collapsed = []
    by_amount = {}
    for txn in transactions:
        amt_key = round(abs(txn.amount), 2)  # rounding to 2 decimals for comparison
        by_amount.setdefault(amt_key, []).append(txn)

    for txn in transactions:
        if getattr(txn, "category", "").lower() != "transfer" or txn in seen:
            collapsed.append(txn)
            continue

        possible_matches = by_amount.get(round(abs(txn.amount), 2), [])
        found = None
        for other in possible_matches:
            if other is txn or other in seen or other.account_id == txn.account_id:
                continue
            if (
                abs((txn.date - other.date).days) <= date_epsilon
                and (abs(txn.amount) == abs(other.amount))
                and (
                    (txn.amount < 0 and other.amount > 0)
                    or (txn.amount > 0 and other.amount < 0)
                )
            ):
                found = other
                break
        if found:
            seen.add(txn)
            seen.add(found)
            collapsed.append(
                {
                    "type": "transfer",
                    "from_account": txn.account_id
                    if txn.amount < 0
                    else found.account_id,
                    "to_account": txn.account_id
                    if txn.amount > 0
                    else found.account_id,
                    "amount": abs(txn.amount),
                    "date": min(txn.date, found.date),
                    "originals": [txn, found],
                }
            )
        else:
            collapsed.append(txn)
    return collapsed


def deduplicate_transactions(transactions, amount_epsilon=0.01, date_epsilon=1):
    seen = set()
    deduped = []
    for i, txn in enumerate(transactions):
        if txn in seen:
            continue
        for other in transactions[i + 1 :]:
            if other in seen:
                continue
            if (
                abs(txn.amount - other.amount) <= amount_epsilon
                and abs((txn.date - other.date).days) <= date_epsilon
                and txn.description == other.description
            ):
                seen.add(other)
        deduped.append(txn)
    return deduped
