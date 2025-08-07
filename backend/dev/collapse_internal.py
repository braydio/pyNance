

def collapse_internal_transfers(transactions, date_epsilon=1, amount_epsilon=0.01):
    seen = set()
    collapsed = []

    # Pre-group by abs(amount) for quick match
    by_amount = {}
    for txn in transactions:
        if abs(txn.amount) not in by_amount:
            by_amount[abs(txn.amount)] = []
        by_amount[abs(txn.amount)].append(txn)

    for txn in transactions:
        if txn.transaction_id in seen:
            continue
        if getattr(txn, "category", "").lower() != "transfer":
            collapsed.append(txn)
            continue

        matches = by_amount.get(abs(txn.amount), [])
        found = None
        for m in matches:
            if m.transaction_id == txn.transaction_id or m.account_id == txn.account_id:
                continue
            if abs((txn.date - m.date).days) <= date_epsilon and (
                txn.amount + m.amount
            ) in [-amount_epsilon, 0, amount_epsilon]:
                if getattr(m, "category", "").lower() == "transfer":
                    found = m
                    break
        if found:
            # Collapse as a pair
            seen.add(found.transaction_id)
            seen.add(txn.transaction_id)
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
