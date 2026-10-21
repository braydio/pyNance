"""Read-only explanation of why Money Out differs from economic expenses for a date range.

Reports counts and amounts only, grouped by source account and posting month. No merchant names,
memos or transaction ids are returned, so a report can be shared without leaking ledger rows.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Iterable

from app.services.account_portfolio_metrics import classify_account_group
from app.services.transaction_flow_classification import (
    _cash_component,
    _cents,
    rollup_by_day,
    rollup_cash_movement_by_day,
)


def _dollars(cents: int) -> float:
    return round(cents / 100, 2)


def build_cash_flow_diagnostic(flows: Iterable[SimpleNamespace]) -> dict[str, Any]:
    """Summarise economic versus cash outgo and the rows that explain the gap."""
    flows = list(flows)
    days = rollup_by_day(flows)
    cash_days, coverage = rollup_cash_movement_by_day(flows)

    economic_expenses = -sum((d["expenses"] for d in days.values()), Decimal("0"))
    economic_cents = int((economic_expenses * 100).to_integral_value())
    money_out = sum(d["money_out"] for d in cash_days.values())
    components: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "cents": 0})
    by_account: dict[str, dict[str, Any]] = {}
    flagged_internal_without_pair = {"count": 0, "cents": 0}
    non_funding_by_group: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "cents": 0})

    for flow in flows:
        component = _cash_component(flow)
        if component is None:
            if flow.signed_account_delta is not None:
                group = classify_account_group(flow.account)
                non_funding_by_group[group]["count"] += 1
                non_funding_by_group[group]["cents"] += _cents(flow.signed_account_delta)
            continue
        cents = _cents(flow.signed_account_delta)
        components[component]["count"] += 1
        components[component]["cents"] += cents
        if "unpaired_own_account" in (flow.reason_codes or []):
            flagged_internal_without_pair["count"] += 1
            flagged_internal_without_pair["cents"] += cents
        account_id = str(getattr(flow.account, "account_id", ""))
        entry = by_account.setdefault(
            account_id,
            {
                "account_id": account_id,
                "account_name": getattr(flow.account, "name", None),
                "months": defaultdict(lambda: {"out_cents": 0, "in_cents": 0}),
            },
        )
        month = flow.day.strftime("%Y-%m")
        key = (
            "out_cents"
            if flow.signed_account_delta < 0 and component.endswith("_out") and not component.startswith("verified")
            else "in_cents"
        )
        if component.startswith("verified"):
            continue
        entry["months"][month][key] += cents

    return {
        "basis": "cash_movement",
        "money_out": _dollars(money_out),
        "economic_expenses": _dollars(economic_cents),
        "money_out_minus_economic_expenses": _dollars(money_out - economic_cents),
        "components": {
            name: {"count": v["count"], "amount": _dollars(v["cents"])} for name, v in sorted(components.items())
        },
        "flagged_internal_without_verified_pair": {
            "count": flagged_internal_without_pair["count"],
            "amount": _dollars(flagged_internal_without_pair["cents"]),
        },
        "non_funding_legs_excluded": {
            group: {"count": v["count"], "amount": _dollars(v["cents"])}
            for group, v in sorted(non_funding_by_group.items())
        },
        "by_account": [
            {
                "account_id": e["account_id"],
                "account_name": e["account_name"],
                "months": [
                    {"month": m, "out": _dollars(v["out_cents"]), "in": _dollars(v["in_cents"])}
                    for m, v in sorted(e["months"].items())
                ],
            }
            for e in by_account.values()
        ],
        "coverage": coverage,
        "notes": [
            "Money Out counts cash-account debits once; card and loan purchases are economic only.",
            "Hidden and pending transactions are not loaded, so they are not in either figure.",
        ],
    }
