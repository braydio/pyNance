"""Canonical per-account portfolio metrics (grouping, owed amounts, credit utilization).

Everything here is derived from persisted provider data and keeps unknowns as
``None``: a missing credit limit never becomes ``0`` and derived headroom is never
presented as issuer-reported available credit.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from app.utils.finance_utils import normalize_account_balance

GROUPS = ("depository", "investment", "credit", "loan", "other")
_CREDIT_TYPES = {"credit", "credit card", "credit_card"}
_LOAN_TYPES = {"loan", "liability"}
DEFAULT_STALE_AFTER = timedelta(hours=48)


def classify_account_group(account: Any) -> str:
    """Return one of ``GROUPS`` for an account-like object."""

    if getattr(account, "is_investment", False):
        return "investment"
    kind = (getattr(account, "type", None) or "").strip().lower()
    if kind in _CREDIT_TYPES:
        return "credit"
    if kind in _LOAN_TYPES:
        return "loan"
    if kind == "depository":
        return "depository"
    return "other"


def _as_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def compute_account_metrics(
    account: Any,
    *,
    now: datetime | None = None,
    stale_after: timedelta = DEFAULT_STALE_AFTER,
) -> dict[str, Any]:
    """Compute display-safe metrics for ``account``.

    Returns:
        ``group``, ``signed_balance`` (liabilities negative), ``owed`` (liabilities
        only, never negative), ``credit_limit``, ``utilization_pct`` (cards with a
        positive limit only), ``overlimit``, ``available_credit`` plus its
        ``available_credit_source`` (``provider`` | ``derived`` | ``None``), and
        ``balance_status`` (``fresh`` | ``stale`` | ``unknown``).
    """

    group = classify_account_group(account)
    signed = normalize_account_balance(
        getattr(account, "balance", None) or Decimal("0"),
        getattr(account, "type", None),
        account_id=getattr(account, "account_id", None),
    )
    signed = _as_decimal(signed)
    is_liability = group in {"credit", "loan"}
    owed = max(-signed, Decimal("0")) if (is_liability and signed is not None) else None

    limit = _as_decimal(getattr(account, "credit_limit", None)) if group == "credit" else None
    utilization = None
    overlimit = None
    available_credit = None
    available_source = None
    if group == "credit":
        provider_available = _as_decimal(getattr(account, "available_balance", None))
        if limit is not None and limit > 0 and owed is not None:
            utilization = round(float(owed / limit * 100), 2)
            overlimit = owed > limit
        if provider_available is not None:
            available_credit, available_source = provider_available, "provider"
        elif limit is not None and limit > 0 and owed is not None:
            available_credit, available_source = max(limit - owed, Decimal("0")), "derived"

    as_of = _as_utc(getattr(account, "balance_as_of", None))
    if as_of is None:
        status = "unknown"
    else:
        current = _as_utc(now) or datetime.now(timezone.utc)
        status = "stale" if current - as_of > stale_after else "fresh"

    return {
        "group": group,
        "signed_balance": signed,
        "owed": owed,
        "credit_limit": limit,
        "utilization_pct": utilization,
        "overlimit": overlimit,
        "available_credit": available_credit,
        "available_credit_source": available_source,
        "balance_as_of": as_of,
        "balance_status": status,
    }
