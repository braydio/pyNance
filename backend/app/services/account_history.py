"""Utilities for computing account balance history via reverse mapping.

This module exposes helper functions to reconstruct historical daily
balances for an account given its current balance and a sequence of
transactions. It is used by the `/api/accounts/<id>/history` endpoint.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable, List, Dict


def compute_balance_history(
    starting_balance: float,
    transactions: Iterable[Dict[str, float]],
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
    deltas = defaultdict(float)
    for tx in transactions:
        deltas[tx["date"]] += tx["amount"]

    results: List[Dict[str, float]] = []
    balance = starting_balance
    current = end_date
    while current >= start_date:
        results.append({"date": current.isoformat(), "balance": round(balance, 2)})
        balance -= deltas.get(current, 0.0)
        current -= timedelta(days=1)

    results.reverse()
    return results
