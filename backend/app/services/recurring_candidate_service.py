"""Recurring-stream candidates built on the single Forecast V2 recurrence detector.

``detect_candidate_streams`` is a thin, deterministic façade over
``forecast.v2_sources.infer_candidate_streams`` so the review inventory and the forecast cannot
disagree. Inputs are canonical account deltas (``+`` inflow / ``-`` outflow, see
``transaction_semantics``); the sign is normalized exactly once, at the database adapter
(``load_v2_source_data``), never here and never with display amounts.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from forecast.v2_core import _read, _to_date, expand_scheduled_events
from forecast.v2_sources import _next_anchor, infer_candidate_streams

CANDIDATE_VERSION = "v1"
EVIDENCE_LIMIT = 24
MIN_CYCLES_FOR_READY = 3


def candidate_key(user_id: str, account_id: str, merchant_key: str, sign: int, cadence: str, tier: int) -> str:
    """Stable identity for a candidate across rescans and pending-to-posted changes.

    ``tier`` is the cluster's rank by ascending amount within the same merchant/sign, so separate
    plan tiers of one merchant get separate keys while a drifting variable bill keeps its key.
    """
    raw = "|".join((user_id, account_id, merchant_key, str(sign), cadence, CANDIDATE_VERSION, str(tier)))
    return hashlib.sha256(raw.encode()).hexdigest()


def _expected_next(stream: Mapping[str, Any], as_of: date) -> Optional[date]:
    spec = {
        "source_id": "candidate",
        "kind": "scheduled_income" if stream["sign"] > 0 else "scheduled_bill",
        "amount": stream["amount"],
        "account_id": stream["account_id"],
        "cadence": stream["cadence"],
        "anchor_date": _next_anchor(stream),
        "days": stream.get("days"),
    }
    events = expand_scheduled_events([spec], as_of + timedelta(days=1), as_of + timedelta(days=800))
    return events[0].date if events else None


def detect_candidate_streams(
    transactions: Iterable[Any],
    accounts: Iterable[Any],
    as_of: date | str,
    lookback_days: int = 400,
    options: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Return deterministic candidate records plus history coverage.

    Args:
        transactions: Canonical-delta rows (``transaction_id``, ``account_id``, ``date``, ``amount``,
            ``pending``, ``is_internal`` ...). Optional ``raw_amount`` is echoed into evidence.
        accounts: Caller-authorized accounts (``account_id``, ``type``, ``subtype``, ``user_id``).
            Accounts without an owner produce no candidates.
        as_of: Last date of data to use (no look-ahead).
        lookback_days: History window (default 400 so yearly patterns can show two cycles).

    Returns:
        ``{"candidates": [...], "history": {...}, "rejected": {...}}``. Candidates are sorted by
        ``candidate_key`` and contain ``candidate_key, user_id, account_id, merchant_key, label,
        sign, signed_median, amount_min, amount_max, amount_mode, cadence, expected_next_date,
        observations, confidence, reason_codes, ready, evidence``. ``ready`` is true only with at
        least three consistent cycles; two cycles stay ``needs_review_insufficient_cycles``.
    """
    as_of_date = _to_date(as_of, field_name="as_of_date")
    account_list = list(accounts)
    owners = {str(_read(a, "account_id")): _read(a, "user_id") for a in account_list}
    tx_list = list(transactions)
    raw_by_id = {str(_read(t, "transaction_id")): _read(t, "raw_amount") for t in tx_list}
    found = infer_candidate_streams(
        transactions=tx_list,
        accounts=account_list,
        as_of_date=as_of_date,
        lookback_days=lookback_days,
        options=options,
    )
    candidates = []
    for stream in found["streams"]:
        owner = owners.get(stream["account_id"])
        if not owner or stream["cadence"] is None:
            continue
        key = candidate_key(
            str(owner), stream["account_id"], stream["merchant_key"], stream["sign"], stream["cadence"], stream["tier"]
        )
        members = sorted(stream["transactions"], key=lambda t: (t["_date"], t["transaction_id"]))
        observations = len(stream["dates"])
        candidates.append(
            {
                "candidate_key": key,
                "user_id": str(owner),
                "account_id": stream["account_id"],
                "merchant_key": stream["merchant_key"],
                "label": stream["merchant_key"],
                "sign": stream["sign"],
                "signed_median": stream["amount"],
                "amount_min": stream["amount_min"],
                "amount_max": stream["amount_max"],
                "amount_mode": stream["amount_mode"],
                "cadence": stream["cadence"],
                "expected_next_date": _expected_next(stream, as_of_date),
                "last_observed": stream["last_seen"],
                "observations": observations,
                "confidence": stream["confidence"],
                "reason_codes": list(stream["reason_codes"]),
                "ready": observations >= MIN_CYCLES_FOR_READY,
                "evidence": [
                    {
                        "transaction_id": t["transaction_id"],
                        "date": t["_date"],
                        "amount": t["_amount"],
                        "raw_amount": raw_by_id.get(t["transaction_id"]),
                    }
                    for t in members[-EVIDENCE_LIMIT:]
                ],
            }
        )
    candidates.sort(key=lambda c: c["candidate_key"])
    return {"candidates": candidates, "history": found["history"], "rejected": found["rejected"]}


def money(value: Decimal) -> str:
    """Format a candidate amount as cents text."""
    return f"{value:.2f}"


__all__ = ["candidate_key", "detect_candidate_streams", "money"]
