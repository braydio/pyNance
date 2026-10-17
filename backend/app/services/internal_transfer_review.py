"""Owner-scoped internal transfer candidate search and pair-confirmation checks.

Matching is evidence based and read-only: nothing here sets ``is_internal``. A scan only ever
reads the trusted owner's own accounts, in a bounded date range, and compares **canonical account
deltas** (see ``app.services.transaction_semantics``). Rows whose sign is unknown are skipped.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterable, Optional

from app.extensions import db
from app.models import Account, Transaction
from app.services.transaction_semantics import normalize_amount

UTC = timezone.utc
TWOPLACES = Decimal("0.01")
AMOUNT_EPSILON = TWOPLACES
DEFAULT_RANGE_DAYS = 90
MAX_RANGE_DAYS = 365
MAX_ROWS = 2000
MAX_PAIRS = 100

INTERNAL_TRANSFER_KEYWORDS = {"transfer", "zelle", "venmo", "cashapp", "cash app", "payment", "p2p", "xfer"}
NON_TRANSFER_KEYWORDS = {
    "uber",
    "ubereats",
    "eats",
    "doordash",
    "grubhub",
    "lyft",
    "restaurant",
    "grocery",
    "groceries",
    "amazon",
    "target",
    "walmart",
    "shell",
    "chevron",
    "starbucks",
    "netflix",
    "spotify",
}


class TransferReviewError(Exception):
    """Validation failure; ``status`` is the HTTP status a route should return."""

    status = 400


class OwnerRequired(TransferReviewError):
    status = 503


class Forbidden(TransferReviewError):
    status = 403


class NotFound(TransferReviewError):
    status = 404


class Conflict(TransferReviewError):
    status = 409


# --------------------------------------------------------------------------- scoring helpers


def normalize_txn_datetime(value: date | datetime | None) -> datetime:
    """Convert a transaction calendar date to UTC midnight for interval scoring."""
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=UTC)
    return datetime.min.replace(tzinfo=UTC)


def tokenize_transfer_text(value: Optional[str]) -> set[str]:
    """Extract lowercase alphanumeric tokens from transfer descriptions."""
    return set(re.findall(r"[a-z0-9]+", value.lower())) if value else set()


def _has_hint(tokens: set[str], raw_text: Optional[str], keywords: set[str]) -> bool:
    if raw_text and any(keyword in raw_text.lower() for keyword in keywords):
        return True
    return any(token in keywords for token in tokens)


def has_transfer_hint(tokens: set[str], raw_text: Optional[str] = None) -> bool:
    """Whether text contains common transfer/payment words."""
    return _has_hint(tokens, raw_text, INTERNAL_TRANSFER_KEYWORDS)


def has_non_transfer_hint(tokens: set[str], raw_text: Optional[str] = None) -> bool:
    """Whether text looks like normal merchant spend."""
    return _has_hint(tokens, raw_text, NON_TRANSFER_KEYWORDS)


def internal_match_score(
    anchor: dict,
    candidate: dict,
    max_window_seconds: float,
    amount_epsilon: Decimal,
    allow_same_account: bool,
) -> Optional[float]:
    """Score an internal-transfer candidate pair; lower is better, ``None`` means ineligible.

    ``amount`` on both records is the canonical account delta, so offsetting means opposite signs.
    """
    if anchor["transaction_id"] == candidate["transaction_id"]:
        return None
    if not allow_same_account and anchor["account_id"] == candidate["account_id"]:
        return None

    amount_a, amount_b = anchor["amount"], candidate["amount"]
    if amount_a == 0 or amount_b == 0 or amount_a * amount_b >= 0:
        return None
    amount_delta = abs(abs(amount_a) - abs(amount_b))
    if amount_delta > amount_epsilon:
        return None
    time_delta_seconds = abs((anchor["date"] - candidate["date"]).total_seconds())
    if time_delta_seconds > max_window_seconds:
        return None

    score = float(amount_delta * Decimal("1000")) + time_delta_seconds / 3600.0
    score += 6.0 if anchor["account_id"] == candidate["account_id"] else -0.5

    overlap = anchor["tokens"] & candidate["tokens"]
    if overlap:
        score -= min(2.0, 0.5 * len(overlap))

    hint_a = has_transfer_hint(anchor["tokens"], anchor.get("description"))
    hint_b = has_transfer_hint(candidate["tokens"], candidate.get("description"))
    if hint_a and hint_b:
        score -= 4.0
    elif hint_a or hint_b:
        score += 12.0  # transfer-looking rows must not pair with ordinary merchant spend

    if has_non_transfer_hint(anchor["tokens"], anchor.get("description")) and not hint_a:
        score += 6.0
    if has_non_transfer_hint(candidate["tokens"], candidate.get("description")) and not hint_b:
        score += 6.0
    return score


# --------------------------------------------------------------------------- scan


def _resolve_range(start_date: Optional[date], end_date: Optional[date]) -> tuple[date, date]:
    end = end_date or datetime.now(UTC).date()
    start = start_date or end - timedelta(days=DEFAULT_RANGE_DAYS - 1)
    if start > end:
        raise TransferReviewError("start_date must not be after end_date")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise TransferReviewError(f"date range is limited to {MAX_RANGE_DAYS} days")
    return start, end


def _record(txn: Transaction, account: Account, delta: Decimal) -> dict[str, Any]:
    description = txn.description or txn.merchant_name or ""
    return {
        "transaction_id": txn.transaction_id,
        "account_id": txn.account_id,
        "account_label": " / ".join(part for part in (account.institution_name, account.name) if part)
        or "Unknown account",
        "amount": delta,
        "date": normalize_txn_datetime(txn.date),
        "description": description,
        "merchant": txn.merchant_name if txn.merchant_name not in (None, "", "Unknown") else description,
        "tokens": tokenize_transfer_text(description),
    }


def _side(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "transaction_id": record["transaction_id"],
        "date": record["date"].date().isoformat(),
        "account_label": record["account_label"],
        "merchant": record["merchant"],
        "amount": float(record["amount"]),
    }


def _evidence(anchor: dict, other: dict, same_account: bool) -> dict[str, Any]:
    gap = abs(abs(anchor["amount"]) - abs(other["amount"]))
    days = abs((anchor["date"] - other["date"]).days)
    shared = sorted(anchor["tokens"] & other["tokens"])
    keyword = has_transfer_hint(anchor["tokens"], anchor["description"]) and has_transfer_hint(
        other["tokens"], other["description"]
    )
    strong = not same_account and gap == 0 and days <= 2 and bool(shared or keyword)
    return {
        "amount_gap_cents": int((gap * 100).to_integral_value()),
        "day_gap": days,
        "shared_tokens": shared,
        "transfer_keyword": keyword,
        "low_confidence": not strong,
    }


def find_candidates(
    owner_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_ids: Optional[Iterable[str]] = None,
    max_rows: int = MAX_ROWS,
    allow_same_account: bool = False,
    date_window_days: int = 3,
    amount_epsilon: Decimal = AMOUNT_EPSILON,
    max_pairs: int = MAX_PAIRS,
) -> dict[str, Any]:
    """Return candidate transfer pairs for one owner. Read-only; never mutates transactions.

    Filtering happens in SQL on the account owner **and** the transaction owner, then on posted,
    not-yet-internal rows inside a bounded date range (default 90 days, hard cap 365). At most
    ``max_rows`` rows are examined (newest first) and ``max_pairs`` pairs returned; the response says
    when either limit truncated the result. No user identifiers are returned.
    """
    if not owner_id:
        raise OwnerRequired("A trusted owner is required to scan for transfers")
    start, end = _resolve_range(start_date, end_date)
    max_rows = max(1, min(int(max_rows), MAX_ROWS))
    max_pairs = max(1, min(int(max_pairs), MAX_PAIRS))

    query = (
        db.session.query(Transaction, Account)
        .join(Account, Transaction.account_id == Account.account_id)
        .filter(Account.user_id == owner_id)
        .filter((Transaction.user_id == owner_id) | (Transaction.user_id.is_(None)))
        .filter((Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None)))
        .filter((Transaction.pending.is_(False)) | (Transaction.pending.is_(None)))
        .filter(Transaction.date >= start, Transaction.date < end + timedelta(days=1))
    )
    wanted = {str(a) for a in account_ids} if account_ids else None
    if wanted:
        query = query.filter(Transaction.account_id.in_(sorted(wanted)))
    rows = query.order_by(Transaction.date.desc(), Transaction.transaction_id).limit(max_rows + 1).all()
    rows_truncated = len(rows) > max_rows
    rows = rows[:max_rows]

    records = []
    skipped_unknown_sign = 0
    for txn, account in rows:
        sign = normalize_amount(provider=getattr(txn.provider, "value", txn.provider), raw_amount=txn.amount)
        if sign.delta is None or sign.delta == 0:
            skipped_unknown_sign += 1
            continue
        records.append(_record(txn, account, sign.delta.quantize(TWOPLACES)))
    records.sort(key=lambda r: (r["date"], r["transaction_id"]))

    window = float(date_window_days * 86400)
    pairs: list[dict[str, Any]] = []
    seen: set[str] = set()
    pairs_truncated = False
    for index, anchor in enumerate(records):
        if anchor["transaction_id"] in seen:
            continue
        best, best_score = None, None
        for candidate in records[index + 1 :]:
            if candidate["transaction_id"] in seen:
                continue
            if (candidate["date"] - anchor["date"]).total_seconds() > window:
                break
            score = internal_match_score(anchor, candidate, window, amount_epsilon, allow_same_account)
            if score is None:
                continue
            same = anchor["account_id"] == candidate["account_id"]
            if same:  # same-account correction needs exact amounts and a transfer keyword on both rows
                evidence = _evidence(anchor, candidate, True)
                if evidence["amount_gap_cents"] or not evidence["transfer_keyword"]:
                    continue
            if best_score is None or score < best_score:
                best, best_score = candidate, score
        if best is None:
            continue
        if len(pairs) >= max_pairs:
            pairs_truncated = True
            break
        outflow, inflow = (anchor, best) if anchor["amount"] < 0 else (best, anchor)
        evidence = _evidence(anchor, best, anchor["account_id"] == best["account_id"])
        pairs.append(
            {
                "pair_id": "~".join(sorted((anchor["transaction_id"], best["transaction_id"]))),
                "left": _side(outflow),
                "right": _side(inflow),
                "evidence": evidence,
                "confidence_label": "review" if evidence["low_confidence"] else "strong",
                "_score": best_score,
            }
        )
        seen.update((anchor["transaction_id"], best["transaction_id"]))

    pairs.sort(key=lambda p: (p["confidence_label"] != "strong", p.pop("_score")))
    return {
        "pairs": pairs,
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "scanned_rows": len(rows),
        "skipped_unknown_sign": skipped_unknown_sign,
        "truncated": rows_truncated or pairs_truncated,
        "truncation": {"rows": rows_truncated, "pairs": pairs_truncated},
    }


# --------------------------------------------------------------------------- confirmation


def _owned(owner_id: str, txn: Transaction) -> Account:
    account = Account.query.filter_by(account_id=txn.account_id).first()
    if account is None or account.user_id != owner_id or (txn.user_id and txn.user_id != owner_id):
        raise Forbidden("Transaction is not available to this user")
    return account


def authorize_internal_flag(
    owner_id: str,
    txn: Transaction,
    counterpart_id: Optional[str],
    is_internal: bool,
    allow_same_account: bool = False,
) -> tuple[Optional[Transaction], bool]:
    """Validate an ``is_internal`` change before anything is mutated.

    Returns ``(counterpart_or_None, already_linked)``. ``already_linked`` is true when confirming a
    pair that is already confirmed in both directions, so a replay is a harmless no-op.

    Raises:
        OwnerRequired: no trusted owner.
        Forbidden: either transaction belongs to a different owner.
        NotFound: the counterpart does not exist.
        Conflict: pending rows, same-sign rows, or a one-to-one linkage conflict.
        TransferReviewError: missing/same ids or an unexpected same-account pair.
    """
    if not owner_id:
        raise OwnerRequired("A trusted owner is required to change transfer flags")
    _owned(owner_id, txn)
    if not counterpart_id:
        return None, False
    if counterpart_id == txn.transaction_id:
        raise TransferReviewError("A transaction cannot be its own counterpart")
    other = Transaction.query.filter_by(transaction_id=counterpart_id).first()
    if other is None:
        raise NotFound("Counterpart transaction not found")
    _owned(owner_id, other)
    if not is_internal:
        return other, False

    if txn.account_id == other.account_id and not allow_same_account:
        raise TransferReviewError("Same-account pairs require explicit confirmation")
    if txn.pending or other.pending:
        raise Conflict("Pending transactions cannot be confirmed as transfers")
    signs = [
        normalize_amount(provider=getattr(t.provider, "value", t.provider), raw_amount=t.amount).delta
        for t in (txn, other)
    ]
    if None in signs or signs[0] == 0 or signs[1] == 0 or signs[0] * signs[1] >= 0:
        raise Conflict("Transfer legs must move money in opposite directions")
    if txn.internal_match_id not in (None, other.transaction_id) or other.internal_match_id not in (
        None,
        txn.transaction_id,
    ):
        raise Conflict("One of these transactions is already paired with another transaction")
    already = bool(
        txn.is_internal
        and other.is_internal
        and txn.internal_match_id == other.transaction_id
        and other.internal_match_id == txn.transaction_id
    )
    return other, already
