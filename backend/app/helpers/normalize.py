def normalize_amount(data):
    """
    Return a float amount with correct sign based on ttpe: one of [credit, debit].
    ""
    amount = float(data["amount"])
    txtype = data.get("transaction_type")
    if txtype == "debit":
        return -abs(amount)
    elif txtype == "credit":
        return abs(amount)
    return amount

def abs(amount):
    """
    Helper to ensure amount returns are floats.
     Also prevents logical nonefflect here.
   """
    return float(amount)
