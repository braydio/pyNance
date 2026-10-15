"""Observed interest charges and guarded effective-rate estimation for credit accounts.

Design rules (TP-20261014-006):

* Interest *paid* is observable from posted transactions and is always reportable.
* A contractual APR is only ever *reported* by a provider or *entered* manually.
* An effective annualized charge rate may be estimated only from >= 2 complete
  statement cycles with a verified interest-bearing average daily balance (ADB).
  Reconstructed balance history is never a verified ADB.
* Anything less defensible returns ``None`` plus a reason, never a guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from statistics import median
from typing import Any, Iterable, Sequence

APR_SOURCES = ("provider", "manual", "estimated", "legacy_unverified")
_SOURCE_RANK = {None: 0, "legacy_unverified": 0, "estimated": 1, "manual": 2, "provider": 3}

CREDIT_TYPES = {"credit", "credit card", "credit_card"}
INTEREST_PFC_DETAILED = {"BANK_FEES_INTEREST_CHARGE"}
# Exact (normalized) descriptions only; "interest" substrings also match credits,
# savings interest earned and unrelated merchants.
INTEREST_DESCRIPTIONS = {
    "interest charge",
    "interest charged",
    "purchase interest charge",
    "interest charge on purchases",
    "interest charge on cash advances",
    "interest charge on balance transfers",
    "finance charge",
}
_LEGACY_CATEGORY_PATHS = (["bank fees", "interest charge"], ["interest", "interest charged"])
MIN_CYCLES = 2
MAX_CYCLE_GAP_DAYS = 3
MAX_DISPERSION = 0.25  # (max - min) / median of per-cycle rates
VERIFIED_BALANCE_SOURCES = {"statement", "observed_daily"}


def _normalize_description(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _field(txn: Any, name: str) -> Any:
    return txn.get(name) if isinstance(txn, dict) else getattr(txn, name, None)


def is_credit_card_account(account: Any) -> bool:
    """True only for credit-card products (loans and portfolios have no qualifying data)."""

    kind = str(getattr(account, "type", "") or "").strip().lower()
    subtype = str(getattr(account, "subtype", "") or "").strip().lower()
    return kind in CREDIT_TYPES or subtype in CREDIT_TYPES


def is_qualifying_interest_charge(txn: Any) -> bool:
    """Return True for a posted, positive (charge) transaction that is clearly interest.

    Excludes pending rows, interest credits/reversals (negative amounts), generic bank
    fees, and anything whose only evidence is the word "interest" in a description.
    """

    if _field(txn, "pending"):
        return False
    try:
        amount = Decimal(str(_field(txn, "amount")))
    except Exception:
        return False
    if amount <= 0:
        return False

    pfc = _field(txn, "personal_finance_category") or {}
    if str(pfc.get("detailed") or "").upper() in INTEREST_PFC_DETAILED:
        return True

    category = _field(txn, "category")
    if isinstance(category, (list, tuple)):
        path = [str(part or "").strip().lower() for part in category]
        if any(path[: len(expected)] == expected for expected in _LEGACY_CATEGORY_PATHS):
            return True

    return _normalize_description(_field(txn, "name") or _field(txn, "description")) in INTEREST_DESCRIPTIONS


def qualifying_interest_charges(transactions: Iterable[Any]) -> list[Any]:
    """Filter ``transactions`` to qualifying charges, dropping duplicated events.

    A re-delivered event (same account, date, amount and description under a different
    id) is counted once.
    """

    seen: set[tuple] = set()
    charges = []
    for txn in transactions:
        if not is_qualifying_interest_charge(txn):
            continue
        key = (
            _field(txn, "account_id"),
            str(_field(txn, "date")),
            str(Decimal(str(_field(txn, "amount")))),
            _normalize_description(_field(txn, "name") or _field(txn, "description")),
        )
        if key in seen:
            continue
        seen.add(key)
        charges.append(txn)
    return charges


def interest_paid_between(transactions: Iterable[Any], start: date, end: date) -> Decimal:
    """Total qualifying interest charged on ``start..end`` inclusive (exact period)."""

    total = Decimal("0")
    for txn in qualifying_interest_charges(transactions):
        posted = _field(txn, "date")
        if isinstance(posted, str):
            posted = date.fromisoformat(posted[:10])
        if start <= posted <= end:
            total += Decimal(str(_field(txn, "amount")))
    return total


def recent_interest_by_account(accounts: Sequence[Any], *, days: int = 90, today: date | None = None) -> dict:
    """Observed interest per credit-card account over the trailing ``days`` (one query).

    Returns ``{account_id: {total, charge_count, window_days, since, through, source}}``.
    Non-card accounts are omitted so callers serialize ``None``.
    """

    from app.models import Transaction  # local import keeps the pure helpers importable in isolation

    cards = [a for a in accounts if is_credit_card_account(a)]
    if not cards:
        return {}
    through = today or date.today()
    since = through - timedelta(days=days - 1)
    rows = (
        Transaction.query.filter(
            Transaction.account_id.in_([a.account_id for a in cards]),
            Transaction.date >= since,
            Transaction.date <= through,
            Transaction.pending.is_(False),
            Transaction.amount > 0,
        )
        .order_by(Transaction.date)
        .all()
    )
    by_account: dict[str, list] = {a.account_id: [] for a in cards}
    for row in rows:
        by_account[row.account_id].append(row)
    result = {}
    for account_id, txns in by_account.items():
        charges = qualifying_interest_charges(txns)
        result[account_id] = {
            "total": float(sum((Decimal(str(t.amount)) for t in charges), Decimal("0"))),
            "charge_count": len(charges),
            "window_days": days,
            "since": since.isoformat(),
            "through": through.isoformat(),
            "source": "transactions",
        }
    return result


@dataclass(frozen=True)
class StatementCycle:
    """One complete statement cycle with a *verified* interest-bearing balance."""

    start: date
    end: date
    interest_paid: Decimal
    average_interest_bearing_balance: Decimal | None
    balance_source: str  # "statement" | "observed_daily"; reconstructed history does NOT qualify
    mixed_apr: bool = False  # promo / multi-bucket balances in the cycle

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def _no_estimate(reason: str, cycles: int = 0) -> dict:
    return {"estimated_rate": None, "confidence": None, "sample_cycles": cycles, "reason": reason}


def estimate_effective_rate(cycles: Sequence[StatementCycle]) -> dict:
    """Estimate the effective annualized interest rate (percent) or explain why not.

    The result is an *effective annualized charge rate*, never a confirmed contractual APR.
    Per cycle: ``100 * interest / ADB * 365 / days``; the reported value weights cycles by
    ``ADB * days``.
    """

    if len(cycles) < MIN_CYCLES:
        return _no_estimate("insufficient_cycles", len(cycles))
    ordered = sorted(cycles, key=lambda c: c.start)
    for cycle in ordered:
        if cycle.days <= 0:
            return _no_estimate("invalid_cycle", len(ordered))
        if cycle.balance_source not in VERIFIED_BALANCE_SOURCES:
            return _no_estimate("unverified_balance", len(ordered))
        adb = cycle.average_interest_bearing_balance
        if adb is None or adb <= 0:
            return _no_estimate("no_interest_bearing_balance", len(ordered))
        if cycle.interest_paid < 0:
            return _no_estimate("invalid_interest", len(ordered))
        if cycle.mixed_apr:
            return _no_estimate("mixed_apr_buckets", len(ordered))
    for earlier, later in zip(ordered, ordered[1:]):
        gap = (later.start - earlier.end).days - 1
        if gap < 0 or gap > MAX_CYCLE_GAP_DAYS:
            return _no_estimate("cycles_not_contiguous", len(ordered))

    rates = [float(100 * c.interest_paid / c.average_interest_bearing_balance * Decimal(365) / c.days) for c in ordered]
    mid = median(rates)
    if mid <= 0:
        return _no_estimate("no_interest_observed", len(ordered))
    if (max(rates) - min(rates)) / mid > MAX_DISPERSION:
        return _no_estimate("high_dispersion", len(ordered))

    weighted_balance_days = sum(c.average_interest_bearing_balance * c.days for c in ordered)
    total_interest = sum((c.interest_paid for c in ordered), Decimal("0"))
    estimate = float(100 * total_interest / weighted_balance_days * Decimal(365))
    return {
        "estimated_rate": round(estimate, 2),
        "confidence": "high" if len(ordered) >= 3 else "medium",
        "sample_cycles": len(ordered),
        "reason": None,
        "kind": "effective_annualized_charge_rate",
    }


def load_verified_cycles(account: Any) -> list[StatementCycle]:
    """Return verified statement cycles for ``account``.

    No verified interest-bearing ADB source exists yet (Plaid liabilities statement data
    arrives with TP-20261014-007), and reconstructed balance history must not stand in for
    one, so this is intentionally empty and ``estimated_rate`` stays ``None``.
    """

    return []


def can_overwrite_apr(current_source: str | None, new_source: str) -> bool:
    """Provider > manual > estimated > legacy/unknown; an estimate never replaces reported data."""

    if new_source not in APR_SOURCES:
        raise ValueError(f"Unknown APR source: {new_source}")
    return _SOURCE_RANK[new_source] >= _SOURCE_RANK.get(current_source, 0)


def apply_apr(account: Any, value: Any, source: str, *, as_of=None, details=None, confidence=None, cycles=None) -> bool:
    """Set ``account.apr`` (percentage units) honoring provenance precedence.

    Returns ``True`` when the account was updated.
    """

    if not can_overwrite_apr(getattr(account, "apr_source", None), source):
        return False
    if value is not None:
        rate = Decimal(str(value))
        if rate < 0 or rate > 200:
            raise ValueError("APR must be a percentage between 0 and 200 (e.g. 23.49, not 0.2349)")
        account.apr = rate
    account.apr_source = source
    account.apr_as_of = as_of
    account.apr_confidence = confidence
    account.apr_sample_cycles = cycles
    if details is not None:
        account.apr_details = details
    return True


def is_contractual_apr(account: Any) -> bool:
    """Only provider-reported or manually entered rates may be shown as the card's APR."""

    return getattr(account, "apr", None) is not None and getattr(account, "apr_source", None) in {"provider", "manual"}
