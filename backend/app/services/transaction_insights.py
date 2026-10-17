"""Owner-scoped transaction insights over every matching row (never a paginated slice).

Summary numbers come from the shared economic-flow classifier
(``transaction_flow_classification``), so spending, refunds, income and transfers here agree with
Daily Net and the financial summary. Review items use a few defensible, rule-based heuristics with
visible evidence; nothing is auto-edited, nothing is removed, and no external or LLM service is used.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterable, Optional

from sqlalchemy import func

from app.extensions import db
from app.models import Account, RecurringStream, Transaction
from app.services.transaction_flow_classification import load_classified_flows

MAX_RANGE_DAYS = 366
MAX_ROWS = 20000
MAX_REVIEW_ITEMS = 20
IDS_PER_ITEM = 10
CACHE_TTL_SECONDS = 600
UNCATEGORIZED = {"", "uncategorized", "unknown", "none"}

_CACHE: dict[tuple, tuple[float, dict[str, Any]]] = {}


class InsightsError(Exception):
    """Invalid request scope; ``status`` is the HTTP status a route should return."""

    status = 400


def invalidate_insights_cache() -> None:
    """Drop cached insights (called whenever transactions are edited or refreshed)."""
    _CACHE.clear()


def _cents(value: Decimal) -> float:
    return round(float(value), 2)


def _resolve_range(start: Optional[date], end: Optional[date], today: Optional[date]) -> tuple[date, date]:
    end = end or today or datetime.now(timezone.utc).date()
    start = start or end - timedelta(days=29)
    if start > end:
        raise InsightsError("start_date must not be after end_date")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise InsightsError(f"date range is limited to {MAX_RANGE_DAYS} days")
    return start, end


def _is_uncategorized(tx: Any) -> bool:
    return str(tx.category or "").strip().lower() in UNCATEGORIZED


def _merchant(tx: Any) -> str:
    name = str(tx.merchant_name or "").strip()
    return "" if name.lower() in {"", "unknown"} else name


def _item(kind: str, priority: int, flows: list, explanation: str, evidence: list[str], filter_: dict) -> dict:
    total = sum((abs(f.signed_account_delta) for f in flows if f.signed_account_delta is not None), Decimal(0))
    return {
        "id": f"{kind}:{flows[0].tx.transaction_id}",
        "kind": kind,
        "priority": priority,
        "count": len(flows),
        "amount_total": _cents(total),
        "transaction_ids": [f.tx.transaction_id for f in flows[:IDS_PER_ITEM]],
        "explanation": explanation,
        "evidence": evidence,
        "filter": filter_,
    }


def _review_items(flows: list) -> list[dict[str, Any]]:
    """Rule-based review items, highest priority first, capped at ``MAX_REVIEW_ITEMS``."""
    items: list[dict[str, Any]] = []

    unconfirmed = [
        f
        for f in flows
        if f.flow_kind == "unclassified"
        and any("unpaired" in reason or "unconfirmed" in reason for reason in f.reason_codes)
    ]
    if unconfirmed:
        items.append(
            _item(
                "transfer_candidate",
                1,
                unconfirmed,
                f"{len(unconfirmed)} transfer-looking transactions are not matched to another of your accounts, "
                "so they are left out of income and spending until you review them.",
                ["Provider labels them as transfers", "No matching transaction on another account is confirmed"],
                {"review": "transfer_candidate"},
            )
        )

    groups: dict[tuple, list] = defaultdict(list)
    for f in flows:
        merchant = _merchant(f.tx)
        if f.flow_kind == "expense" and merchant and f.signed_account_delta is not None:
            groups[(f.tx.account_id, merchant.lower(), f.signed_account_delta, f.day)].append(f)
    for (_, _, amount, day), group in sorted(groups.items(), key=lambda kv: (kv[0][3], str(kv[0][2])), reverse=True):
        if len(group) < 2:
            continue
        merchant = _merchant(group[0].tx)
        items.append(
            _item(
                "possible_duplicate_same_merchant_amount_day",
                2,
                group,
                f"Possible duplicate: {len(group)} charges of {abs(amount):.2f} at {merchant} on {day.isoformat()}. "
                "They may be separate purchases.",
                ["Same account", "Same merchant", "Same amount", "Same day"],
                {"search": merchant, "start_date": day.isoformat(), "end_date": day.isoformat()},
            )
        )

    fees = [f for f in flows if f.flow_kind == "expense" and any("fee" in r for r in f.reason_codes)]
    if fees:
        items.append(
            _item(
                "bank_fee",
                2,
                fees,
                f"{len(fees)} bank fees or interest charges in this period.",
                ["Provider category is bank fees or interest"],
                {"category_contains": "fee"},
            )
        )

    missing = [f for f in flows if f.flow_kind in {"income", "expense"} and _is_uncategorized(f.tx)]
    if missing:
        items.append(
            _item(
                "missing_category",
                3,
                missing,
                f"{len(missing)} transactions have no category, so they are grouped as Uncategorized.",
                ["Category is empty or Uncategorized"],
                {"uncategorized": True},
            )
        )
    items.sort(key=lambda i: (i["priority"], -i["amount_total"]))
    return items[:MAX_REVIEW_ITEMS]


def get_insights(
    owner_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_ids: Optional[Iterable[str]] = None,
    categories: Optional[Iterable[str]] = None,
    *,
    today: Optional[date] = None,
    refresh: bool = False,
) -> dict[str, Any]:
    """Summarize ALL posted, visible transactions for ``owner_id`` in the range.

    Returns ``matching_count`` (SQL ``COUNT``), ``gross_spend``, ``refunds``, ``net_spend``,
    ``income`` (economic only), ``inflow`` (economic income versus every credit movement with
    transfer / refund / unclassified subtotals), ``fees``, ``uncategorized_count``,
    ``review_items`` (<= 20), ``recurring_candidate_count``, ``transfer_pair_count`` and ``coverage``.
    Cached for ten minutes per owner and filters; ``refresh=True`` recomputes.
    """
    if not owner_id:
        raise InsightsError("A trusted owner is required")
    start, end = _resolve_range(start_date, end_date, today)
    ids = tuple(sorted({str(a) for a in account_ids})) if account_ids else ()
    wanted = tuple(sorted({str(c) for c in categories})) if categories else ()
    key = (owner_id, start, end, ids, wanted)
    cached = _CACHE.get(key)
    if cached and not refresh and cached[0] > time.time():
        return {**cached[1], "cache": {"hit": True}}

    count_query = (
        db.session.query(func.count(Transaction.id))
        .join(Account, Transaction.account_id == Account.account_id)
        .filter(Account.user_id == owner_id)
        .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
        .filter((Transaction.pending.is_(False)) | (Transaction.pending.is_(None)))
        .filter((Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None)))
        .filter(Transaction.date >= start, Transaction.date <= end)
    )
    if ids:
        count_query = count_query.filter(Transaction.account_id.in_(ids))
    if wanted:
        count_query = count_query.filter(Transaction.category.in_(wanted))
    matching_count = int(count_query.scalar() or 0)

    flows = load_classified_flows(owner_id, start, end, account_ids=ids or None)
    if wanted:
        flows = [f for f in flows if f.tx.category in wanted]
    truncated = len(flows) > MAX_ROWS
    flows = flows[:MAX_ROWS]

    zero = Decimal("0.00")
    totals = defaultdict(lambda: zero)
    for f in flows:
        delta = f.signed_account_delta
        if delta is None:
            continue
        if delta > 0:
            totals["all_credits"] += delta
        if f.flow_kind == "expense":
            totals["gross_spend"] += -delta
            if any("fee" in r for r in f.reason_codes):
                totals["fees"] += -delta
        elif f.flow_kind == "refund":
            totals["refunds"] += delta
        elif f.flow_kind == "income":
            totals["income"] += delta
        elif delta > 0:
            totals[f"{f.flow_kind}_in"] += delta

    recurring_candidates = RecurringStream.query.filter_by(
        user_id=owner_id, status="proposed", source="detected"
    ).count()
    from app.services import internal_transfer_review

    try:
        transfer_pairs = len(internal_transfer_review.find_candidates(owner_id, start, end, ids or None)["pairs"])
    except internal_transfer_review.TransferReviewError:
        transfer_pairs = 0

    payload = {
        "matching_count": matching_count,
        "pending_excluded": True,
        "gross_spend": _cents(totals["gross_spend"]),
        "refunds": _cents(totals["refunds"]),
        "net_spend": _cents(totals["gross_spend"] - totals["refunds"]),
        "income": _cents(totals["income"]),
        "inflow": {
            "economic_income": _cents(totals["income"]),
            "all_credit_movements": _cents(totals["all_credits"]),
            "refunds": _cents(totals["refunds"]),
            "transfers_in": _cents(totals["transfer_in"]),
            "debt_settlement_in": _cents(totals["debt_settlement_in"]),
            "investment_in": _cents(totals["investment_movement_in"]),
            "unclassified_in": _cents(totals["unclassified_in"]),
        },
        "fees": _cents(totals["fees"]),
        "uncategorized_count": sum(
            1 for f in flows if f.flow_kind in {"income", "expense"} and _is_uncategorized(f.tx)
        ),
        "review_items": _review_items(flows),
        "recurring_candidate_count": recurring_candidates,
        "transfer_pair_count": transfer_pairs,
        "coverage": {
            "range": {"start": start.isoformat(), "end": end.isoformat()},
            "rows_considered": len(flows),
            "truncated": truncated,
            "unclassified_count": sum(1 for f in flows if f.flow_kind == "unclassified"),
            "basis": "economic_flow",
        },
    }
    _CACHE[key] = (time.time() + CACHE_TTL_SECONDS, payload)
    return {**payload, "cache": {"hit": False}}
