"""Single sign contract for turning stored transaction amounts into account deltas.

``transactions.amount`` keeps whatever the provider sent and is never rewritten. Forecast code
works in **canonical account deltas**: positive means the account balance went up (deposit,
refund, debt paid down on a liability account), negative means it went down.

Per-provider table:

========  ===========================================  ================================
provider  stored ``amount``                            canonical delta
========  ===========================================  ================================
plaid     ``+`` debit/outflow, ``-`` credit/inflow     ``-amount`` (cash and liability)
manual    no direction stored on the row               ``manual_direction`` required
========  ===========================================  ================================

Plaid examples: checking purchase ``+60`` -> ``-60``; paycheck ``-1000`` -> ``+1000``;
card purchase ``+90`` -> ``-90`` on the card (debt up, no cash has left a bank yet);
card payment ``-90`` -> ``+90`` on the card (debt down).

Manual rows carry no direction indicator in the database, so a manual amount is only used when the
caller supplies one of ``MANUAL_DIRECTIONS``. Otherwise the result is ``None`` and the row is
diagnosed as ``sign_unknown`` instead of being assumed to be an expense.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from forecast.v2_core import classify_forecast_account

SIGN_UNKNOWN = "sign_unknown"
INVALID_AMOUNT = "invalid_amount"

# ``signed`` means the stored amount already follows ``+ inflow / - outflow`` (verified by the caller).
MANUAL_DIRECTIONS = {
    "inflow": 1,
    "credit": 1,
    "income": 1,
    "outflow": -1,
    "debit": -1,
    "expense": -1,
    "signed": 0,
}
CENT = Decimal("0.01")


@dataclass(frozen=True)
class AmountSemantics:
    """Result of normalizing one stored amount.

    Attributes:
        delta: Canonical account delta, or ``None`` when it cannot be determined.
        semantics: ``plaid_provider_sign``, ``manual_<direction>`` or a diagnostic code.
        warning: ``SIGN_UNKNOWN`` / ``INVALID_AMOUNT`` when ``delta`` is ``None``.
    """

    delta: Optional[Decimal]
    semantics: str
    warning: Optional[str] = None


def _to_finite_decimal(value: Any) -> Optional[Decimal]:
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return amount if amount.is_finite() else None


def normalize_amount(
    *,
    provider: Optional[str],
    raw_amount: Any,
    account_type: Any = None,
    manual_direction: Optional[str] = None,
) -> AmountSemantics:
    """Return the canonical delta for one stored amount plus how it was derived.

    Args:
        provider: ``plaid`` or ``manual`` (case-insensitive). Anything else is unknown.
        raw_amount: Stored ``Transaction.amount``; never modified.
        account_type: Accepted for call-site symmetry. Plaid's sign is the same for cash and
            liability accounts, so it does not change the delta.
        manual_direction: One of ``MANUAL_DIRECTIONS`` for manual rows.
    """
    del account_type  # same sign rule for every account bucket; bucket handling lives in the V2 pipeline
    amount = _to_finite_decimal(raw_amount)
    if amount is None:
        return AmountSemantics(None, INVALID_AMOUNT, INVALID_AMOUNT)
    kind = str(provider or "").strip().lower()
    if kind == "plaid":
        return AmountSemantics(-amount if amount else Decimal(0), "plaid_provider_sign")
    if kind == "manual":
        direction = str(manual_direction or "").strip().lower()
        if direction not in MANUAL_DIRECTIONS:
            return AmountSemantics(None, SIGN_UNKNOWN, SIGN_UNKNOWN)
        factor = MANUAL_DIRECTIONS[direction]
        delta = amount if factor == 0 else abs(amount) * factor
        return AmountSemantics(delta, f"manual_{direction}")
    return AmountSemantics(None, SIGN_UNKNOWN, SIGN_UNKNOWN)


def canonical_account_delta(
    *,
    provider: Optional[str],
    raw_amount: Any,
    account_type: Any = None,
    manual_direction: Optional[str] = None,
) -> Optional[Decimal]:
    """Return the canonical account delta as ``Decimal`` or ``None`` when the sign is unknown."""
    return normalize_amount(
        provider=provider,
        raw_amount=raw_amount,
        account_type=account_type,
        manual_direction=manual_direction,
    ).delta


def account_bucket(account: Any) -> str:
    """Bucket an account (``cash``, ``liability``, ``investment``, ``other_asset``, ``unknown``)."""
    return classify_forecast_account(account)


__all__ = [
    "AmountSemantics",
    "INVALID_AMOUNT",
    "MANUAL_DIRECTIONS",
    "SIGN_UNKNOWN",
    "account_bucket",
    "canonical_account_delta",
    "normalize_amount",
]
