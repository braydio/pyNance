"""Utilities for computing account balance history via reverse mapping.

This module exposes helper functions to reconstruct historical daily
balances for an account given its current balance and a sequence of
transactions. It is used by the `/api/accounts/<id>/history` endpoint.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Dict


def compute_balance_history(
    starting_balance: Decimal,
    transactions: Iterable[Dict[str, Decimal]],
    start_date: date,
    end_date: date,
) -> List[Dict[str, float]]:
    """Reverse-map daily balances for an account.

    Args:
        starting_balance: Known balance on ``end_date``.
        transactions: Iterable of transactions with ``date`` (``date``)
            and ``amount`` (float) fields.
        start_date: Earliest date to include, inclusive.
        end_date: Latest date to include, inclusive. Represents the date
            of ``starting_balance``.

    Returns:
        A list of ``{"date": str, "balance": float}`` dictionaries ordered
        by ascending date covering every day in the range.
    """
    # Aggregate transaction deltas by date for quick lookup.
    # Use Decimal throughout to avoid floating point inaccuracies.
    deltas: Dict[date, Decimal] = defaultdict(Decimal)
    for tx in transactions:
        amount = tx["amount"]
        if not isinstance(amount, Decimal):
            # Coerce floats/ints/strings to Decimal safely
            amount = Decimal(str(amount))
        deltas[tx["date"]] += amount

    results: List[Dict[str, float]] = []
    balance: Decimal = starting_balance
    current = end_date
    while current >= start_date:
        # Quantize to 2 decimal places for currency, then serialize as float
        quantized = balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        results.append({"date": current.isoformat(), "balance": float(quantized)})
        balance -= deltas.get(current, Decimal("0"))
        current -= timedelta(days=1)

    results.reverse()
    return results
