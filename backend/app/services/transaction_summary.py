"""Whole-population totals for a filtered Activity table.

``summarize_transactions`` builds its relation with the same
``account_logic.build_transaction_filter_query`` as the paginated table, so the totals describe every
matching row regardless of page or sort. Amounts come from the shared economic-flow classifier
exactly once: only income, expense and refund rows are economic; movement between accounts, debt
settlement, investment movement and unclassified rows are reported beside them and never inside
``economic_net``. Read-only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.models import Transaction
from app.services.transaction_flow_classification import classify_rows
from app.sql import account_logic

ZERO = Decimal("0.00")


def _money(value: Decimal) -> float:
    return round(float(value), 2)


def _group() -> dict[str, Any]:
    return {"income": ZERO, "expenses": ZERO, "refunds": ZERO, "count": 0}


def _serialize_groups(groups: dict[str, dict[str, Any]], labels: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for key, group in groups.items():
        net = group["income"] + group["expenses"] + group["refunds"]
        rows.append(
            {
                "key": key,
                "label": labels.get(key, key),
                "income": _money(group["income"]),
                "expenses": _money(group["expenses"]),
                "refunds": _money(group["refunds"]),
                "economic_net": _money(net),
                "count": group["count"],
            }
        )
    return rows


def summarize_transactions(owner_id: str, filters: dict[str, Any], *, applied: dict[str, Any] | None = None) -> dict:
    """Return the ``all_matching`` summary for ``filters`` (kwargs of ``build_transaction_filter_query``).

    Owner-bound through the account; hidden accounts, pending rows and rows owned by someone else
    are excluded. ``pending_excluded_count`` reports how many otherwise-matching pending rows were
    left out so the table count and this summary can be reconciled.
    """
    if not owner_id:
        raise ValueError("owner_id is required for transaction summaries")
    scoped = {**filters, "user_id": owner_id}
    base = account_logic.build_transaction_filter_query(**scoped, exclude_pending=True).filter(
        (Transaction.user_id == owner_id) | (Transaction.user_id.is_(None))
    )
    flows = classify_rows(base.all())
    pending_excluded = (
        account_logic.build_transaction_filter_query(**scoped)
        .filter(Transaction.pending.is_(True))
        .order_by(None)
        .count()
    )

    totals = {key: ZERO for key in ("income", "expenses", "refunds")}
    movement = {
        key: ZERO
        for key in (
            "transfers_in",
            "transfers_out",
            "debt_settlements",
            "investment_movements",
            "unclassified_in",
            "unclassified_out",
        )
    }
    by_category: dict[str, dict[str, Any]] = {}
    by_account: dict[str, dict[str, Any]] = {}
    by_month: dict[str, dict[str, Any]] = {}
    labels: dict[str, dict[str, str]] = {"category": {}, "account": {}, "month": {}}
    needs_review = 0
    latest_day = None

    for flow in flows:
        delta, kind = flow.signed_account_delta, flow.flow_kind
        if latest_day is None or (flow.day and flow.day > latest_day):
            latest_day = flow.day
        if delta is None or kind == "unclassified":
            needs_review += 1
            if delta is not None:
                movement["unclassified_in" if delta > 0 else "unclassified_out"] += abs(delta)
            continue
        if kind == "transfer":
            movement["transfers_in" if delta > 0 else "transfers_out"] += abs(delta)
            continue
        if kind == "debt_settlement":
            movement["debt_settlements"] += abs(delta)
            continue
        if kind == "investment_movement":
            movement["investment_movements"] += abs(delta)
            continue
        field = {"income": "income", "expense": "expenses", "refund": "refunds"}.get(kind)
        if field is None:
            needs_review += 1
            continue
        totals[field] += delta
        category = flow.tx.category or "Uncategorized"
        account_key = str(flow.tx.account_id)
        month = flow.day.strftime("%Y-%m") if flow.day else "unknown"
        labels["category"][category] = category
        labels["account"][account_key] = flow.account.name or account_key
        labels["month"][month] = month
        for groups, key in ((by_category, category), (by_account, account_key), (by_month, month)):
            group = groups.setdefault(key, _group())
            group[field] += delta
            group["count"] += 1

    economic_net = totals["income"] + totals["expenses"] + totals["refunds"]
    return {
        "scope": "all_matching",
        "matching_count": len(flows),
        "income": _money(totals["income"]),
        "expenses": _money(totals["expenses"]),
        "refunds": _money(totals["refunds"]),
        "economic_net": _money(economic_net),
        **{key: _money(value) for key, value in movement.items()},
        "needs_review_count": needs_review,
        "pending_excluded_count": pending_excluded,
        "breakdowns": {
            "by_category": sorted(_serialize_groups(by_category, labels["category"]), key=lambda r: r["economic_net"]),
            "by_account": sorted(_serialize_groups(by_account, labels["account"]), key=lambda r: r["label"]),
            "by_month": sorted(_serialize_groups(by_month, labels["month"]), key=lambda r: r["key"]),
        },
        "latest_transaction_date": latest_day.isoformat() if latest_day else None,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "applied_filters": applied or {},
    }


__all__ = ["summarize_transactions"]
