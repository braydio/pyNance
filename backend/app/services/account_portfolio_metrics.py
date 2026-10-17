"""Canonical per-account portfolio metrics (grouping, owed amounts, credit utilization).

Everything here is derived from persisted provider data and keeps unknowns as
``None``: a missing credit limit never becomes ``0`` and derived headroom is never
presented as issuer-reported available credit.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from app.utils.finance_utils import normalize_account_balance

GROUPS = ("depository", "investment", "credit", "loan", "other")
_CREDIT_TYPES = {"credit", "credit card", "creditcard"}
_LOAN_TYPES = {"loan", "liability", "mortgage", "student", "student loan", "auto", "line of credit", "home equity"}
# Bank-style subtypes identify a spendable deposit account even under an investment-typed item.
_BANK_SUBTYPES = {"checking", "savings", "depository"}
_DEPOSITORY_TYPES = {"depository", "checking", "savings", "cash", "cash management", "money market", "cd"}
_INVESTMENT_PATTERN = re.compile(r"\b(investment|brokerage|ira|roth|401\(?k\)?|403\(?b\)?|retirement|pension)\b")
DEFAULT_STALE_AFTER = timedelta(hours=48)


def _compact(value: Any) -> str:
    """Lowercase and collapse separators so ``credit_card`` and ``Credit Card`` compare equal."""

    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", str(value or "").strip().lower()))


def resolve_classification(account: Any) -> tuple[str, str]:
    """Return ``(group, reason)`` using the same precedence as the frontend portfolio.

    Explicit type/subtype wins over the legacy ``is_investment`` flag, because a provider can type a
    whole item as "investment" while each account's subtype says what it really is (a Robinhood
    "Credit card" or "Savings"). Precedence: credit, loan, investment subtype, bank-style subtype
    (checking/savings), investment type, depository, then the flag, then ``other``.
    """

    kind = _compact(getattr(account, "account_type", None) or getattr(account, "type", None))
    sub = _compact(getattr(account, "subtype", None))
    if kind in _CREDIT_TYPES or sub in _CREDIT_TYPES:
        return "credit", "explicit_credit"
    if kind in _LOAN_TYPES or sub in _LOAN_TYPES:
        return "loan", "explicit_loan"
    if _INVESTMENT_PATTERN.search(sub):
        return "investment", "investment_subtype"
    if sub in _BANK_SUBTYPES:
        return "depository", "bank_subtype"
    if _INVESTMENT_PATTERN.search(kind):
        return "investment", "investment_type"
    if kind in _DEPOSITORY_TYPES or sub in _DEPOSITORY_TYPES:
        return "depository", "depository_type"
    if getattr(account, "is_investment", False):
        return "investment", "is_investment_flag"
    return "other", "unrecognized"


def classify_account_group(account: Any) -> str:
    """Return one of ``GROUPS`` for an account-like object."""

    return resolve_classification(account)[0]


def classification_conflict(account: Any) -> dict[str, str] | None:
    """Describe a legacy ``is_investment`` flag that disagrees with the explicit type/subtype."""

    if not getattr(account, "is_investment", False):
        return None
    group, reason = resolve_classification(account)
    if group in {"investment", "other"}:
        return None
    return {"flag": "is_investment", "classified": group, "reason": reason}


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
        ``balance_status`` (``fresh`` | ``stale`` | ``unknown``) and
        ``classification_conflict`` (``None`` or the legacy-flag mismatch description).
    """

    group = classify_account_group(account)
    signed = normalize_account_balance(
        getattr(account, "balance", None) or Decimal("0"),
        getattr(account, "type", None),
        account_id=getattr(account, "account_id", None),
        subtype=getattr(account, "subtype", None),
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
        "classification_conflict": classification_conflict(account),
    }
