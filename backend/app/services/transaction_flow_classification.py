"""Read-only economic-flow classification for reporting (Daily Net, summaries, transaction lists).

A bank balance moving is not the same thing as earning or spending. ``classify_reporting_flow``
sorts each posted transaction into one ``flow_kind`` without touching the stored row:

=================== ===================================================================
``income``           wages, interest, dividends and other income with category evidence
``expense``          ordinary spending, fees and interest charges
``refund``           money back for a purchase; offsets expense, never counts as income
``transfer``         confirmed or verified movement between the owner's own accounts
``debt_settlement``  paying a card or loan; the purchase was already the spending event
``investment_movement`` contributions/withdrawals to investment and retirement funds
``unclassified``     a credit or debit with no defensible meaning: shown for review, never
                     silently counted as income or spending
=================== ===================================================================

The bank's signed amount is preserved (``signed_account_delta`` is the canonical account delta from
``transaction_semantics``); ``economic_amount`` is only set for income, expense and refund. Nothing
here sets ``is_internal`` or creates pairs: unpaired transfer evidence stays ``unclassified``.
Free-text memos are never used as proof of an own-account transfer.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Iterable, Optional

from app.extensions import db
from app.models import Account, Transaction
from app.services.account_portfolio_metrics import classify_account_group
from app.services.transaction_semantics import canonical_account_delta

FLOW_KINDS = (
    "income",
    "expense",
    "refund",
    "transfer",
    "debt_settlement",
    "investment_movement",
    "unclassified",
)
CENT = Decimal("0.01")

_INCOME_PREFIX = "INCOME_"
_REFUND_WORDS = ("refund", "reversal", "chargeback", "return of", "credit adjustment")
_ECONOMIC_KINDS = {"income", "expense", "refund"}


@dataclass(frozen=True)
class LinkedPair:
    """A counterpart transaction and its account, supplied only when the link is verified."""

    tx: Any
    account: Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _pfc(tx: Any) -> tuple[str, str]:
    """Return Plaid personal-finance ``(primary, detailed)`` upper-case, or empty strings."""
    raw = getattr(tx, "personal_finance_category", None)
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = None
    if isinstance(raw, dict):
        return _text(raw.get("primary")).upper(), _text(raw.get("detailed")).upper()
    return "", ""


def user_decision_for(tx: Any) -> Optional[str]:
    """Derive a trusted user correction from stored edit history.

    Returns ``"not_transfer"`` when the user explicitly turned the internal-transfer flag off.
    """
    raw = getattr(tx, "user_modified_fields", None)
    try:
        fields = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
    except (ValueError, TypeError):
        return None
    if fields.get("is_internal") and not getattr(tx, "is_internal", False):
        return "not_transfer"
    return None


def _pair_verified(tx: Any, account: Any, pair: Optional[LinkedPair]) -> bool:
    """A pair counts only when it is reciprocal, same-owner, cross-account and offsetting."""
    if pair is None or pair.tx is None:
        return False
    other, other_account = pair.tx, pair.account
    if getattr(tx, "internal_match_id", None) != getattr(other, "transaction_id", object()):
        return False
    if getattr(other, "internal_match_id", None) != getattr(tx, "transaction_id", object()):
        return False
    owner = getattr(account, "user_id", None)
    if not owner or getattr(other_account, "user_id", None) != owner:
        return False
    if getattr(tx, "account_id", None) == getattr(other, "account_id", None):
        return False
    a = canonical_account_delta(provider=_provider(tx), raw_amount=getattr(tx, "amount", None))
    b = canonical_account_delta(provider=_provider(other), raw_amount=getattr(other, "amount", None))
    return a is not None and b is not None and a != 0 and abs(a + b) <= CENT


def _provider(tx: Any) -> Any:
    provider = getattr(tx, "provider", None)
    return getattr(provider, "value", provider)


def _result(kind: str, confidence: str, reasons: list[str], delta: Optional[Decimal]) -> dict[str, Any]:
    economic = delta if kind in _ECONOMIC_KINDS else None
    return {
        "flow_kind": kind,
        "confidence": confidence,
        "reason_codes": reasons,
        "signed_account_delta": delta,
        "economic_amount": economic,
    }


def classify_reporting_flow(
    tx: Any,
    account: Any,
    *,
    linked_pair: Optional[LinkedPair] = None,
    user_decision: Optional[str] = None,
) -> dict[str, Any]:
    """Classify one transaction for reporting.

    Args:
        tx: Transaction-like row (``provider``, ``amount``, ``is_internal``, ``internal_match_id``,
            ``personal_finance_category``, ``category_slug``, ``description`` ...). Never modified.
        account: The transaction's account (``user_id``, ``type``, ``subtype``, ``is_investment``).
        linked_pair: The reciprocal counterpart, only when the caller found one. It is verified here.
        user_decision: ``"not_transfer"`` when the user explicitly rejected a transfer flag. Takes
            precedence over automatic evidence.

    Returns:
        ``{"flow_kind", "confidence", "reason_codes", "signed_account_delta", "economic_amount"}``.
    """
    delta = canonical_account_delta(provider=_provider(tx), raw_amount=getattr(tx, "amount", None))
    if delta is None:
        return _result("unclassified", "low", ["sign_unknown"], None)
    delta = delta.quantize(CENT)
    if delta == 0:
        return _result("unclassified", "low", ["zero_amount"], delta)

    group = classify_account_group(account)
    primary, detailed = _pfc(tx)
    slug = _text(getattr(tx, "category_slug", None)).lower()
    text = f"{_text(getattr(tx, 'description', None))} {_text(getattr(tx, 'merchant_name', None))}".lower()
    inflow = delta > 0
    user_rejected = user_decision == "not_transfer"

    # 1. Confirmed or verified movement between the owner's own accounts.
    if not user_rejected:
        if getattr(tx, "is_internal", False):
            reason = "confirmed_internal" if getattr(tx, "internal_match_id", None) else "unpaired_own_account"
            return _result("transfer", "high", [reason], delta)
        if _pair_verified(tx, account, linked_pair):
            return _result("transfer", "high", ["verified_pair"], delta)

    # 2. Investment accounts: only income and fees count economically; the rest is movement.
    if group == "investment":
        if primary == "INCOME":
            return _result("income", "medium", ["investment_income"], delta)
        if primary == "BANK_FEES" and not inflow:
            return _result("expense", "medium", ["investment_fee"], delta)
        return _result("investment_movement", "medium", ["investment_account"], delta)

    # 3. Provider evidence on cash and liability accounts.
    if detailed.endswith("INVESTMENT_AND_RETIREMENT_FUNDS"):
        return _result("investment_movement", "medium", ["pfc_investment_transfer"], delta)
    if primary == "LOAN_PAYMENTS":
        return _result("debt_settlement", "medium", ["pfc_loan_payment"], delta)
    if primary == "INCOME" and inflow:
        return _result("income", "medium", [f"pfc_{detailed.lower() or 'income'}"], delta)
    if primary in {"TRANSFER_IN", "TRANSFER_OUT"}:
        if user_rejected:
            return _result("income" if inflow else "expense", "high", ["user_not_transfer"], delta)
        if detailed.endswith("CASH_ADVANCES_AND_LOANS"):
            return _result("unclassified", "low", ["loan_proceeds_not_income"], delta)
        reason = "pfc_account_transfer_unpaired" if "ACCOUNT_TRANSFER" in detailed else "pfc_transfer_unconfirmed"
        return _result("unclassified", "low", [reason], delta)

    # 4. Ordinary movement.
    if inflow:
        if any(word in text for word in _REFUND_WORDS):
            return _result("refund", "medium", ["refund_wording"], delta)
        if primary and primary not in {"INCOME", "TRANSFER_IN", "TRANSFER_OUT", "LOAN_PAYMENTS", "BANK_FEES", "OTHER"}:
            return _result("refund", "medium", [f"credit_in_{primary.lower()}"], delta)
        if "income" in slug or "payroll" in slug or "wages" in slug:
            return _result("income", "medium", ["income_category"], delta)
        return _result("unclassified", "low", ["credit_without_evidence"], delta)
    if primary == "BANK_FEES":
        return _result("expense", "medium", ["pfc_fee_or_interest"], delta)
    return _result("expense", "medium" if primary else "low", ["pfc_expense" if primary else "default_expense"], delta)


# --------------------------------------------------------------------------- loading + rollups


def load_classified_flows(
    owner_id: str,
    start_date: date,
    end_date: date,
    *,
    account_ids: Optional[Iterable[str]] = None,
) -> list[SimpleNamespace]:
    """Classify the owner's posted, visible transactions in ``[start_date, end_date]``.

    One query loads the rows (owner-bound through the account, hidden and pending excluded) and one
    batch loads the counterparts of any ``internal_match_id`` so there is no per-row lookup. Returns
    ``SimpleNamespace(tx, account, day, **classification)`` rows ordered by date.
    """
    if not owner_id:
        raise ValueError("owner_id is required for reporting flows")
    query = (
        db.session.query(Transaction, Account)
        .join(Account, Transaction.account_id == Account.account_id)
        .filter(Account.user_id == owner_id)
        .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
        .filter((Transaction.pending.is_(False)) | (Transaction.pending.is_(None)))
        .filter((Transaction.user_id == owner_id) | (Transaction.user_id.is_(None)))
        .filter(Transaction.date >= start_date, Transaction.date <= end_date)
        .order_by(Transaction.date, Transaction.transaction_id)
    )
    if account_ids:
        query = query.filter(Transaction.account_id.in_([str(a) for a in account_ids]))
    return classify_rows(query.all())


def classify_rows(rows: Iterable[tuple[Any, Any]]) -> list[SimpleNamespace]:
    """Classify ``(Transaction, Account)`` rows with one batched lookup for linked counterparts.

    Callers own the row selection (owner scope, filters); this only classifies. Extra tuple members
    after the account (such as a joined category) are ignored. Returns
    ``SimpleNamespace(tx, account, day, **classification)`` in input order.
    """
    rows = [(row[0], row[1]) for row in rows]
    match_ids = {tx.internal_match_id for tx, _ in rows if tx.internal_match_id}
    counterparts: dict[str, LinkedPair] = {}
    if match_ids:
        for other, other_account in (
            db.session.query(Transaction, Account)
            .join(Account, Transaction.account_id == Account.account_id)
            .filter(Transaction.transaction_id.in_(match_ids))
            .all()
        ):
            counterparts[other.transaction_id] = LinkedPair(other, other_account)

    out: list[SimpleNamespace] = []
    for tx, account in rows:
        day = tx.date.date() if isinstance(tx.date, datetime) else tx.date
        result = classify_reporting_flow(
            tx,
            account,
            linked_pair=counterparts.get(tx.internal_match_id) if tx.internal_match_id else None,
            user_decision=user_decision_for(tx),
        )
        linked = counterparts.get(tx.internal_match_id) if tx.internal_match_id else None
        out.append(
            SimpleNamespace(
                tx=tx,
                account=account,
                day=day,
                linked_account=linked.account if linked else None,
                **result,
            )
        )
    return out


def rollup_by_day(flows: Iterable[SimpleNamespace]) -> dict[str, dict[str, Any]]:
    """Aggregate classified flows per ISO day.

    Economic fields: ``income``, ``expenses`` (negative), ``refunds`` and ``net`` (income + expenses +
    refunds). Cash-movement fields, never part of ``net``: ``transfer_in``/``transfer_out``,
    ``debt_settlement``, ``investment_movement`` and the review buckets ``unclassified_inflows`` /
    ``unclassified_outflows``. ``transaction_count`` counts only rows that behave like activity (not
    confirmed transfers), matching the transactions explorer.
    """
    zero = Decimal("0.00")
    days: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "income": zero,
            "expenses": zero,
            "refunds": zero,
            "transfer_in": zero,
            "transfer_out": zero,
            "debt_settlement": zero,
            "investment_movement": zero,
            "unclassified_inflows": zero,
            "unclassified_outflows": zero,
            "transaction_count": 0,
            "transfer_count": 0,
            "unclassified_count": 0,
        }
    )
    for flow in flows:
        bucket = days[flow.day.isoformat()]
        delta, kind = flow.signed_account_delta, flow.flow_kind
        if delta is None:
            bucket["unclassified_count"] += 1
            bucket["transaction_count"] += 1
            continue
        if kind == "transfer":
            bucket["transfer_count"] += 1
            bucket["transfer_in" if delta > 0 else "transfer_out"] += abs(delta)
            continue
        bucket["transaction_count"] += 1
        if kind == "income":
            bucket["income"] += delta
        elif kind == "expense":
            bucket["expenses"] += delta
        elif kind == "refund":
            bucket["refunds"] += delta
        elif kind == "debt_settlement":
            bucket["debt_settlement"] += abs(delta)
        elif kind == "investment_movement":
            bucket["investment_movement"] += abs(delta)
        else:
            bucket["unclassified_count"] += 1
            bucket["unclassified_inflows" if delta > 0 else "unclassified_outflows"] += abs(delta)
    for bucket in days.values():
        bucket["net"] = bucket["income"] + bucket["expenses"] + bucket["refunds"]
    return dict(days)


# --------------------------------------------------------------------------- cash movement

_P2P_WORDS = ("venmo", "zelle", "cash app", "cashapp", "paypal", "apple cash", "applecash")
_CASH_OUT_PARTS = (
    "direct_payment_out",
    "debt_payment_out",
    "investment_allocation_out",
    "external_person_out",
    "unclassified_out",
)
_CASH_IN_PARTS = ("income_in", "refund_in", "financing_in", "investment_in", "unclassified_in")
_EXCLUDED_PARTS = ("verified_own_transfer_out", "verified_own_transfer_in")


def _cents(value: Decimal) -> int:
    return int((abs(value) * 100).to_integral_value())


def _cash_component(flow: SimpleNamespace) -> Optional[str]:
    """Name the cash-movement component for one funding-account leg, or ``None`` if not a funding leg.

    Only depository (spendable) accounts fund cash movement. Liability and investment account legs
    are the other side of the same event and never count again. A verified transfer to another of
    the owner's cash accounts is excluded; one whose counterpart is a card or loan is a debt payment
    and one whose counterpart is an investment account is an investment allocation.
    """
    delta = flow.signed_account_delta
    if delta is None or classify_account_group(flow.account) != "depository":
        return None
    out = delta < 0
    kind, reasons = flow.flow_kind, set(flow.reason_codes or [])
    if kind == "transfer":
        if "unpaired_own_account" in reasons:
            return "unclassified_out" if out else "unclassified_in"
        partner = classify_account_group(flow.linked_account) if getattr(flow, "linked_account", None) else None
        if partner in {"credit", "loan"}:
            return "debt_payment_out" if out else "financing_in"
        if partner == "investment":
            return "investment_allocation_out" if out else "investment_in"
        return "verified_own_transfer_out" if out else "verified_own_transfer_in"
    if out:
        if kind == "debt_settlement":
            return "debt_payment_out"
        if kind == "investment_movement":
            return "investment_allocation_out"
        if kind == "expense":
            text = f"{_text(getattr(flow.tx, 'description', None))} {_text(getattr(flow.tx, 'merchant_name', None))}".lower()
            return "external_person_out" if any(word in text for word in _P2P_WORDS) else "direct_payment_out"
        return "unclassified_out"
    if kind == "income":
        return "income_in"
    if kind == "refund":
        return "refund_in"
    if kind == "investment_movement":
        return "investment_in"
    if "loan_proceeds_not_income" in reasons:
        return "financing_in"
    return "unclassified_in"


def rollup_cash_movement_by_day(flows: Iterable[SimpleNamespace]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Aggregate actual cash movement of the owner's funding (depository) accounts per ISO day.

    Money Out and Money In are positive integer cents; ``net_cash = money_in - money_out``. Money Out
    is the sum of ``direct_payment_out``, ``debt_payment_out``, ``investment_allocation_out``,
    ``external_person_out`` and ``unclassified_out`` (needs classification). Verified transfers
    between two of the owner's cash accounts are tracked as ``verified_own_transfer_*`` but excluded
    from both totals, so a transfer never counts twice. Card and loan payments count once, at the
    funding leg; the card purchase belongs to the economic view only. This does not replace
    ``rollup_by_day``: the economic rollup is unchanged.

    Returns:
        ``(days, coverage)``; ``coverage`` states which accounts funded the figures and how many
        rows were left out or need review, so an incomplete picture is visible rather than zero.
    """
    flows = list(flows)
    days: dict[str, dict[str, Any]] = defaultdict(
        lambda: {name: 0 for name in (*_CASH_OUT_PARTS, *_CASH_IN_PARTS, *_EXCLUDED_PARTS)}
    )
    funding_accounts: set[str] = set()
    non_funding_legs = funding_legs = 0
    unverified_internal = {"count": 0, "cents": 0}
    for flow in flows:
        component = _cash_component(flow)
        if component is None:
            non_funding_legs += 1
            continue
        funding_legs += 1
        funding_accounts.add(str(getattr(flow.account, "account_id", "")))
        cents = _cents(flow.signed_account_delta)
        days[flow.day.isoformat()][component] += cents
        if "unpaired_own_account" in (flow.reason_codes or []):
            unverified_internal["count"] += 1
            unverified_internal["cents"] += cents
    for bucket in days.values():
        bucket["money_out"] = sum(bucket[name] for name in _CASH_OUT_PARTS)
        bucket["money_in"] = sum(bucket[name] for name in _CASH_IN_PARTS)
        bucket["net_cash"] = bucket["money_in"] - bucket["money_out"]
    coverage = {
        "basis": "cash_movement",
        "scope": "funding_accounts_depository",
        "funding_account_count": len(funding_accounts),
        "funding_leg_count": funding_legs,
        "non_funding_leg_count": non_funding_legs,
        "unverified_internal": unverified_internal,
        "complete": bool(funding_accounts),
        "needs_review": any(b["unclassified_out"] or b["unclassified_in"] for b in days.values()),
    }
    return dict(days), coverage


__all__ = [
    "rollup_cash_movement_by_day",
    "FLOW_KINDS",
    "LinkedPair",
    "classify_reporting_flow",
    "classify_rows",
    "load_classified_flows",
    "rollup_by_day",
    "user_decision_for",
]
