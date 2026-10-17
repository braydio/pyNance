"""Owner-scoped persistence for recurring streams.

Every function takes the owner as an argument and validates account membership **before** any
write. Callers must obtain the owner from ``trusted_owner_id()`` (server-side configuration); a
``user_id`` from a request payload is never accepted. Amounts are ``Decimal`` canonical cash deltas
(``+`` inflow / ``-`` outflow).
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any, Iterable, Optional

from dateutil.relativedelta import relativedelta

from app.extensions import db
from app.models import Account, RecurringStream

CADENCES = ("once", "weekly", "biweekly", "semimonthly", "monthly", "quarterly", "yearly")
AMOUNT_MODES = ("fixed", "variable")
STATUSES = ("proposed", "confirmed", "ignored", "ended")
SOURCES = ("manual", "detected", "legacy")
OWNER_ENV = "PYNANCE_OWNER_USER_ID"
CENT = Decimal("0.01")

_CADENCE_ALIASES = {
    "bi-weekly": "biweekly",
    "every_two_weeks": "biweekly",
    "annual": "yearly",
    "annually": "yearly",
    "semi-monthly": "semimonthly",
}


class RecurringError(Exception):
    """Base class; ``status`` is the HTTP status a route should return."""

    status = 400
    code = "recurring_error"


class OwnerNotConfigured(RecurringError):
    """No trusted server-side owner is configured; mutations fail closed."""

    status = 503
    code = "owner_not_configured"


class AccountNotAvailable(RecurringError):
    """The account does not exist or belongs to someone else (indistinguishable on purpose)."""

    status = 404
    code = "account_not_found"


class StreamNotFound(RecurringError):
    status = 404
    code = "stream_not_found"


class ValidationFailed(RecurringError):
    status = 400
    code = "invalid_stream"


class AmbiguousMatch(RecurringError):
    status = 409
    code = "ambiguous_match"


def trusted_owner_id() -> str:
    """Return the single configured owner (``PYNANCE_OWNER_USER_ID``) or fail closed.

    The app has no authenticated principal, so owner-scoped recurring access is bound to this
    server-only setting. It is never read from a request.
    """
    owner = (os.environ.get(OWNER_ENV) or "").strip()
    if not owner:
        raise OwnerNotConfigured(f"{OWNER_ENV} must be set to enable recurring stream access")
    return owner


def owned_account(owner_id: str, account_id: str) -> Account:
    """Return the account when ``owner_id`` owns it; otherwise raise ``AccountNotAvailable``."""
    account = Account.query.filter_by(account_id=str(account_id or ""), user_id=owner_id).first()
    if account is None:
        raise AccountNotAvailable("Account not found")
    return account


def parse_amount(value: Any) -> Decimal:
    """Parse a finite money amount to cents (``Decimal``); floats go through ``str`` first."""
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationFailed("amount must be a number") from exc
    if not amount.is_finite():
        raise ValidationFailed("amount must be finite")
    return amount.quantize(CENT, rounding=ROUND_HALF_EVEN)


def parse_cadence(value: Any) -> str:
    cadence = str(value or "").strip().lower()
    cadence = _CADENCE_ALIASES.get(cadence, cadence)
    if cadence not in CADENCES:
        raise ValidationFailed(f"cadence must be one of {', '.join(CADENCES)}")
    return cadence


def parse_date(value: Any, field: str = "anchor_date") -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError) as exc:
        raise ValidationFailed(f"{field} must be YYYY-MM-DD") from exc


def merchant_key_for(name: Optional[str]) -> Optional[str]:
    key = " ".join(str(name or "").lower().split())[:160]
    return key or None


def serialize(stream: RecurringStream) -> dict[str, Any]:
    """Return a JSON-safe dict; amounts are strings to keep cents exact."""
    return {
        "id": stream.id,
        "account_id": stream.account_id,
        "display_name": stream.display_name,
        "merchant_key": stream.merchant_key,
        "amount_cash_delta": f"{stream.amount_cash_delta:.2f}",
        "amount_mode": stream.amount_mode,
        "cadence": stream.cadence,
        "anchor_date": stream.anchor_date.isoformat(),
        "status": stream.status,
        "source": stream.source,
        "confidence": None if stream.confidence is None else f"{stream.confidence:.3f}",
        "last_observed": stream.last_observed.isoformat() if stream.last_observed else None,
        "notes": stream.notes,
    }


def create_manual(
    owner_id: str,
    *,
    account_id: str,
    display_name: str,
    amount_cash_delta: Any,
    cadence: Any,
    anchor_date: Any,
    amount_mode: str = "fixed",
    notes: Optional[str] = None,
    source: str = "manual",
    status: str = "confirmed",
    merchant_key: Optional[str] = None,
    confidence: Any = None,
) -> RecurringStream:
    """Create a stream for an owned account. Validates everything before touching the session."""
    account = owned_account(owner_id, account_id)
    name = str(display_name or "").strip()
    if not name:
        raise ValidationFailed("display_name is required")
    if amount_mode not in AMOUNT_MODES:
        raise ValidationFailed("amount_mode must be fixed or variable")
    if status not in STATUSES or source not in SOURCES:
        raise ValidationFailed("invalid status or source")
    amount = parse_amount(amount_cash_delta)
    stream = RecurringStream(
        user_id=owner_id,
        account_id=account.account_id,
        display_name=name[:256],
        merchant_key=merchant_key if merchant_key is not None else merchant_key_for(name),
        amount_cash_delta=amount,
        amount_mode=amount_mode,
        cadence=parse_cadence(cadence),
        anchor_date=parse_date(anchor_date),
        status=status,
        source=source,
        confidence=None if confidence is None else Decimal(str(confidence)).quantize(Decimal("0.001")),
        notes=notes,
        confirmed_at=datetime.now(timezone.utc) if status == "confirmed" else None,
    )
    db.session.add(stream)
    db.session.commit()
    return stream


def get_stream(owner_id: str, stream_id: str) -> RecurringStream:
    stream = RecurringStream.query.filter_by(id=str(stream_id), user_id=owner_id).first()
    if stream is None:
        raise StreamNotFound("Recurring stream not found")
    return stream


_UPDATABLE = {"display_name", "amount_cash_delta", "amount_mode", "cadence", "anchor_date", "status", "notes"}


def update_stream(owner_id: str, stream_id: str, **changes: Any) -> RecurringStream:
    """Update allowed fields of an owned stream; unknown fields are rejected, not ignored."""
    stream = get_stream(owner_id, stream_id)
    unknown = set(changes) - _UPDATABLE
    if unknown:
        raise ValidationFailed(f"cannot update: {', '.join(sorted(unknown))}")
    staged: dict[str, Any] = {}
    for key, value in changes.items():
        if key == "amount_cash_delta":
            staged[key] = parse_amount(value)
        elif key == "cadence":
            staged[key] = parse_cadence(value)
        elif key == "anchor_date":
            staged[key] = parse_date(value)
        elif key == "amount_mode" and value not in AMOUNT_MODES:
            raise ValidationFailed("amount_mode must be fixed or variable")
        elif key == "status" and value not in STATUSES:
            raise ValidationFailed("invalid status")
        elif key == "display_name":
            name = str(value or "").strip()
            if not name:
                raise ValidationFailed("display_name is required")
            staged[key] = name[:256]
        else:
            staged[key] = value
    for key, value in staged.items():
        setattr(stream, key, value)
    if staged.get("status") == "confirmed" and stream.confirmed_at is None:
        stream.confirmed_at = datetime.now(timezone.utc)
    db.session.commit()
    return stream


def delete_or_end_stream(owner_id: str, stream_id: str, *, hard: bool = False) -> str:
    """End an owned stream (default, keeps evidence) or hard-delete it; returns the action taken."""
    stream = get_stream(owner_id, stream_id)
    if hard:
        db.session.delete(stream)
        action = "deleted"
    else:
        stream.status = "ended"
        action = "ended"
    db.session.commit()
    return action


def list_streams(
    owner_id: str,
    *,
    account_id: Optional[str] = None,
    statuses: Optional[Iterable[str]] = None,
) -> list[RecurringStream]:
    """List the owner's streams, optionally narrowed to one owned account and some statuses."""
    if account_id is not None:
        owned_account(owner_id, account_id)
    query = RecurringStream.query.filter_by(user_id=owner_id)
    if account_id is not None:
        query = query.filter_by(account_id=str(account_id))
    if statuses:
        query = query.filter(RecurringStream.status.in_(list(statuses)))
    return query.order_by(RecurringStream.anchor_date, RecurringStream.id).all()


def find_by_name_and_amount(
    owner_id: str, account_id: str, display_name: str, amount_cash_delta: Any
) -> list[RecurringStream]:
    """Streams on an owned account matching name and amount (used by the legacy PUT/DELETE shape)."""
    owned_account(owner_id, account_id)
    amount = parse_amount(amount_cash_delta)
    key = merchant_key_for(display_name)
    return (
        RecurringStream.query.filter_by(user_id=owner_id, account_id=str(account_id), amount_cash_delta=amount)
        .filter(RecurringStream.merchant_key == key)
        .filter(RecurringStream.status != "ended")
        .order_by(RecurringStream.id)
        .all()
    )


_STEP = {
    "weekly": relativedelta(weeks=1),
    "biweekly": relativedelta(weeks=2),
    "monthly": relativedelta(months=1),
    "quarterly": relativedelta(months=3),
    "yearly": relativedelta(years=1),
}


def next_due_date(stream: RecurringStream, today: date) -> Optional[date]:
    """Next occurrence on or after ``today`` (``None`` for a past one-off or an ended stream).

    Month-based steps are computed from the anchor each time so a 31st-of-month plan does not
    drift after a short month. ``semimonthly`` uses the anchor day and the day 15 later in the month.
    """
    if stream.status == "ended":
        return None
    anchor = stream.anchor_date
    if stream.cadence == "once":
        return anchor if anchor >= today else None
    if anchor >= today:
        return anchor
    if stream.cadence == "semimonthly":
        first = anchor.day
        second = first + 15 if first <= 15 else first - 15
        days = sorted({first, second})
        month = today.replace(day=1)
        for offset in range(3):
            base = month + relativedelta(months=offset)
            last = (base + relativedelta(months=1, days=-1)).day
            for day in days:
                candidate = base.replace(day=min(day, last))
                if candidate >= today:
                    return candidate
        return None
    step = _STEP[stream.cadence]
    count = 1
    candidate = anchor + step
    while candidate < today:
        count += 1
        candidate = anchor + step * count
    return candidate


def propose_detected(
    *,
    account_id: str,
    display_name: str,
    amount_cash_delta: Any,
    cadence: Any,
    anchor_date: Any,
    confidence: Any = None,
) -> RecurringStream:
    """Record a detector hit as a ``proposed`` stream without creating any transaction.

    System path (no request principal): the owner is the account's own ``user_id`` from the
    database. An existing stream with the same account, merchant, amount and cadence is refreshed
    instead of duplicated, and a user's confirmed/ignored/ended decision is never overwritten.
    """
    account = Account.query.filter_by(account_id=str(account_id or "")).first()
    if account is None or not account.user_id:
        raise AccountNotAvailable("Account not found or has no owner")
    amount = parse_amount(amount_cash_delta)
    key = merchant_key_for(display_name)
    existing = (
        RecurringStream.query.filter_by(
            user_id=account.user_id,
            account_id=account.account_id,
            merchant_key=key,
            amount_cash_delta=amount,
            cadence=parse_cadence(cadence),
        )
        .order_by(RecurringStream.id)
        .first()
    )
    if existing is not None:
        if existing.status == "proposed":
            existing.anchor_date = parse_date(anchor_date)
            if confidence is not None:
                existing.confidence = Decimal(str(confidence)).quantize(Decimal("0.001"))
            db.session.commit()
        return existing
    return create_manual(
        account.user_id,
        account_id=account.account_id,
        display_name=display_name,
        amount_cash_delta=amount,
        cadence=cadence,
        anchor_date=anchor_date,
        status="proposed",
        source="detected",
        confidence=confidence,
    )
