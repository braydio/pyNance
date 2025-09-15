"""In-memory CRUD service for planning bills and allocations.

This module stores bills and allocation records in simple Python lists.
It provides basic create, read, update, and delete operations used by
planning-related API endpoints. Allocation percentages are validated to
ensure the total does not exceed 100 percent.
"""

from typing import Any, Dict, List

Bill = Dict[str, Any]
Allocation = Dict[str, Any]

BILLS: List[Bill] = []
ALLOCATIONS: List[Allocation] = []


def get_bills() -> List[Bill]:
    """Return all stored bills."""
    return list(BILLS)


def create_bill(bill: Bill) -> Bill:
    """Add a new bill to the in-memory store.

    Args:
        bill: Mapping describing the bill fields.

    Returns:
        The bill that was added.
    """

    BILLS.append(bill)
    return bill


def update_bill(bill_id: str, bill: Bill) -> Bill:
    """Update an existing bill.

    Args:
        bill_id: Identifier of the bill to update.
        bill: Mapping of updated fields for the bill.

    Returns:
        The updated bill.

    Raises:
        ValueError: If the bill ID does not exist.
    """

    for idx, existing in enumerate(BILLS):
        if existing.get("id") == bill_id:
            updated = {**existing, **bill, "id": bill_id}
            BILLS[idx] = updated
            return updated
    raise ValueError(f"Bill {bill_id} not found")


def delete_bill(bill_id: str) -> None:
    """Remove a bill from the store.

    Args:
        bill_id: Identifier of the bill to remove.

    Raises:
        ValueError: If the bill ID does not exist.
    """

    for idx, existing in enumerate(BILLS):
        if existing.get("id") == bill_id:
            BILLS.pop(idx)
            return
    raise ValueError(f"Bill {bill_id} not found")


def get_allocations() -> List[Allocation]:
    """Return all allocation entries."""
    return list(ALLOCATIONS)


def update_allocations(allocations: List[Allocation]) -> List[Allocation]:
    """Replace allocation entries, enforcing a 100% cap.

    Args:
        allocations: Sequence of allocation mappings. Each mapping may
            include a ``percentage`` key indicating its percent share.

    Returns:
        The updated list of allocations.

    Raises:
        ValueError: If the total percentage exceeds 100.
    """

    total_pct = sum(a.get("percentage", 0) for a in allocations)
    if total_pct > 100:
        raise ValueError("Allocation percentages exceed 100%")

    ALLOCATIONS.clear()
    ALLOCATIONS.extend(allocations)
    return list(ALLOCATIONS)
