"""Safe-to-spend dashboard decisioning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import and_, func, or_

from app.extensions import db
from app.models import Account, PlannedBill, PlanningScenario, Transaction

TWOPLACES = Decimal("0.01")
DEFAULT_BUFFER_CENTS = 25_000
DEFAULT_MODE = "today"
# Inclusive day offsets from ``as_of``. ``until_payday`` is the fallback window used when no payday is
# validated (today..today+13 = 14 inclusive days); a validated payday ends the window the day before.
MODE_WINDOWS = {
    "today": 0,
    "week": 6,
    "until_payday": 13,
}
FALLBACK_PROTECTION_DAYS = MODE_WINDOWS["until_payday"]
CALCULATION_VERSION = "2"


def _outflow_filter():
    """Match provider-specific signs for money leaving an account."""

    return or_(
        and_(Transaction.provider == "plaid", Transaction.amount > 0),
        and_(Transaction.provider != "plaid", Transaction.amount < 0),
    )


def _inflow_filter():
    """Match provider-specific signs for money entering an account."""

    return or_(
        and_(Transaction.provider == "plaid", Transaction.amount < 0),
        and_(Transaction.provider != "plaid", Transaction.amount > 0),
    )


@dataclass(frozen=True)
class SafeToSpendInputs:
    """Normalized request inputs for safe-to-spend calculations."""

    user_id: str | None = None
    mode: str = DEFAULT_MODE
    as_of: date | None = None
    buffer_cents: int = DEFAULT_BUFFER_CENTS


def _to_cents(value: Decimal | float | int | None) -> int:
    """Convert a decimal dollar amount into integer cents."""

    amount = Decimal(str(value or 0)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))


def _normalize_mode(mode: str | None) -> str:
    """Return a supported decision horizon, defaulting to today's view."""

    normalized = (mode or DEFAULT_MODE).strip().lower()
    return normalized if normalized in MODE_WINDOWS else DEFAULT_MODE


def _coerce_date(value: date | datetime | str | None) -> date:
    """Return ``value`` as a date, accepting ISO strings for route inputs."""

    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


_NON_SPENDABLE_SUBTYPES = {"cd", "certificate of deposit"}
STALE_BALANCE_AFTER = timedelta(hours=48)


def _is_cash_account(account: Account) -> bool:
    """Return True for owned checking/savings-style accounts; names never qualify an account."""

    from app.services.account_portfolio_metrics import classify_account_group

    if getattr(account, "is_investment", False):
        return False
    if str(getattr(account, "subtype", "") or "").strip().lower() in _NON_SPENDABLE_SUBTYPES:
        return False
    return classify_account_group(account) == "depository"


def _visible_accounts(user_id: str | None = None) -> list[Account]:
    """Load visible accounts, optionally scoped by user."""

    query = Account.query.filter(or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)))
    if user_id:
        query = query.filter(Account.user_id == user_id)
    return query.all()


def _balance_freshness(account: Account, now: datetime) -> str:
    as_of = getattr(account, "balance_as_of", None)
    if as_of is None:
        return "unknown"
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    return "stale" if now - as_of > STALE_BALANCE_AFTER else "fresh"


def _cash_account_payload(accounts: list[Account], now: datetime | None = None) -> tuple[int, list[dict], dict]:
    """Build usable-cash cents, per-account sources and a coverage summary.

    Asset balances keep their sign (an overdraft is a deficit, never ``abs``). Each account
    contributes ``min(current, available)`` when the provider reports both, else ``current`` with an
    ``availability_unverified`` warning. Deficits across eligible accounts are deducted from the
    positive cash before the total is clamped at zero.
    """

    now = now or datetime.now(timezone.utc)
    positive_cents = 0
    deficit_cents = 0
    payload = []
    coverage = {
        "accounts_counted": 0,
        "availability_unverified": 0,
        "stale_balances": 0,
        "unknown_freshness": 0,
        "deficit_accounts": 0,
    }
    for account in accounts:
        if not _is_cash_account(account):
            continue
        current_cents = _to_cents(account.balance)
        available = getattr(account, "available_balance", None)
        warnings = []
        if available is None:
            usable_cents = current_cents
            warnings.append("availability_unverified")
            coverage["availability_unverified"] += 1
        else:
            usable_cents = min(current_cents, _to_cents(available))
        freshness = _balance_freshness(account, now)
        if freshness == "stale":
            coverage["stale_balances"] += 1
            warnings.append("stale_balance")
        elif freshness == "unknown":
            coverage["unknown_freshness"] += 1
            warnings.append("balance_age_unknown")
        if usable_cents < 0:
            deficit_cents += -usable_cents
            coverage["deficit_accounts"] += 1
        else:
            positive_cents += usable_cents
        coverage["accounts_counted"] += 1
        as_of = getattr(account, "balance_as_of", None)
        payload.append(
            {
                "account_id": account.account_id,
                "name": account.display_name,
                "type": account.type,
                "subtype": account.subtype,
                "balance_cents": max(usable_cents, 0),
                "current_balance_cents": current_cents,
                "available_balance_cents": None if available is None else _to_cents(available),
                "deficit_cents": max(-usable_cents, 0),
                "balance_as_of": as_of.isoformat() if as_of else None,
                "balance_status": freshness,
                "warnings": warnings,
            }
        )
    coverage["deficit_cents"] = deficit_cents
    return max(positive_cents - deficit_cents, 0), payload, coverage


def _outflow_filter():
    """Match raw Plaid debits and legacy non-Plaid expenses."""

    return or_(
        and_(Transaction.provider == "plaid", Transaction.amount > 0),
        and_(Transaction.provider != "plaid", Transaction.amount < 0),
    )


def _inflow_filter():
    """Match raw Plaid credits and legacy non-Plaid income."""

    return or_(
        and_(Transaction.provider == "plaid", Transaction.amount < 0),
        and_(Transaction.provider != "plaid", Transaction.amount > 0),
    )


def _spent_between(start: date, end: date, user_id: str | None = None, *, pending: bool = False) -> int:
    """Return posted (or, with ``pending``, pending) non-internal outflows on cash accounts.

    This is a diagnostic: current balances already include posted activity, so it is never
    subtracted from spendable cash. Card purchases and investment accounts are excluded.
    """

    cash_ids = [a.account_id for a in _visible_accounts(user_id) if _is_cash_account(a)]
    if not cash_ids:
        return 0
    query = (
        db.session.query(func.coalesce(func.sum(func.abs(Transaction.amount)), 0))
        .filter(Transaction.account_id.in_(cash_ids))
        .filter(Transaction.date >= start, Transaction.date <= end)
        .filter(_outflow_filter())
        .filter(or_(Transaction.is_internal.is_(False), Transaction.is_internal.is_(None)))
    )
    if pending:
        query = query.filter(Transaction.pending.is_(True))
    else:
        query = query.filter(or_(Transaction.pending.is_(False), Transaction.pending.is_(None)))
    return _to_cents(query.scalar())


_NOT_WAGE_REASONS = ("interest", "dividend", "investment_income", "tax_refund", "retirement")
PAYDAY_LOOKBACK_DAYS = 400


def _payday_owner(user_id: str | None) -> tuple[str | None, str | None]:
    """Return ``(owner_id, refusal_reason)``; payday data is only ever read for the trusted owner."""

    from app.services.recurring_repository import OwnerNotConfigured, trusted_owner_id

    try:
        owner = trusted_owner_id()
    except OwnerNotConfigured:
        return None, "owner_not_configured"
    if user_id and user_id != owner:
        return None, "owner_mismatch"
    return owner, None


def payday_events_for_owner(owner_id: str, as_of: date) -> tuple[list, date | None]:
    """Load posted wage-like cash inflows plus the newest activity date for ``owner_id``.

    Only classified ``income`` on depository accounts counts: internal transfers, refunds, debt and
    brokerage movements, interest/dividends and pending rows are excluded by the shared classifier.
    """

    from app.services.account_portfolio_metrics import classify_account_group
    from app.services.payday_inference import PayEvent, payer_key_for
    from app.services.transaction_flow_classification import load_classified_flows

    flows = load_classified_flows(owner_id, as_of - timedelta(days=PAYDAY_LOOKBACK_DAYS), as_of)
    events = []
    for flow in flows:
        if flow.flow_kind != "income" or classify_account_group(flow.account) != "depository":
            continue
        if any(token in code for code in flow.reason_codes for token in _NOT_WAGE_REASONS):
            continue
        tx = flow.tx
        events.append(
            PayEvent(
                day=flow.day,
                amount=abs(flow.signed_account_delta),
                payer_key=payer_key_for(tx.merchant_name, tx.description),
                account_id=str(tx.account_id),
            )
        )
    return events, (max(f.day for f in flows) if flows else None)


def confirmed_income_streams(owner_id: str, as_of: date) -> list[dict]:
    """Owner-confirmed income streams as detector inputs (next due on/after ``as_of``)."""

    from app.services import recurring_repository as repo

    out = []
    for stream in repo.list_streams(owner_id, statuses=["confirmed"]):
        if stream.event_role != "income" or Decimal(str(stream.amount_cash_delta)) <= 0:
            continue
        if stream.cadence not in {"weekly", "biweekly", "semimonthly", "monthly"}:
            continue
        next_due = repo.next_due_date(stream, as_of)
        if next_due:
            out.append(
                {
                    "name": stream.display_name,
                    "amount": abs(Decimal(str(stream.amount_cash_delta))),
                    "cadence": stream.cadence,
                    "next_due": next_due,
                }
            )
    return out


def _payday_prediction(as_of: date, user_id: str | None = None) -> dict:
    """Run the payday detector against the trusted owner's stored data (no provider calls)."""

    from app.services.payday_inference import infer_payday

    owner, refusal = _payday_owner(user_id)
    if refusal:
        result = infer_payday([], as_of)
        result["reason_codes"] = [refusal]
        return result
    events, data_through = payday_events_for_owner(owner, as_of)
    return infer_payday(
        events, as_of, confirmed_streams=confirmed_income_streams(owner, as_of), data_through=data_through
    )


def _next_income_date(as_of: date, user_id: str | None = None) -> date | None:
    """Legacy adapter: the validated next payday, or ``None`` when evidence is too thin."""

    value = _payday_prediction(as_of, user_id)["next_payday"]
    return date.fromisoformat(value) if value else None


def _windows(mode: str, as_of: date, next_payday: date | None) -> dict:
    """Resolve the inclusive display and protection windows.

    ``protection`` is how far known obligations are reserved: through the day before a validated
    payday, else a labelled 14-day fallback. A payday that is today but not yet posted is never
    assumed to be cash (``awaiting_payday_post``) and also falls back. ``week`` protects at least its
    own 7 days. The display window is only what the label describes; it never shrinks the protection.
    """

    awaiting = next_payday is not None and next_payday <= as_of
    if next_payday is not None and next_payday > as_of:
        protection_end, basis = next_payday - timedelta(days=1), "day_before_payday"
    else:
        protection_end, basis = as_of + timedelta(days=FALLBACK_PROTECTION_DAYS), "fallback_14_day"
    week_end = as_of + timedelta(days=MODE_WINDOWS["week"])
    if mode == "week" and week_end > protection_end:
        protection_end, basis = week_end, "rolling_7_day"
    display_end = {"today": as_of, "week": week_end}.get(mode, protection_end)
    return {
        "display_end": display_end,
        "protection_end": protection_end,
        "basis": basis,
        "awaiting_payday_post": awaiting,
    }


def _window_payload(start: date, end: date, **extra) -> dict:
    return {"start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days + 1, **extra}


def _upcoming_bill_payload(as_of: date, horizon_end: date, user_id: str | None = None) -> tuple[int, list[dict]]:
    """Return planned bills due within the decision horizon."""

    query = PlannedBill.query.join(PlanningScenario).filter(
        PlannedBill.due_date >= as_of, PlannedBill.due_date <= horizon_end
    )
    if user_id:
        query = query.filter(
            PlanningScenario.account_id.in_([account.account_id for account in _visible_accounts(user_id)])
        )

    total = 0
    bills = []
    for bill in query.order_by(PlannedBill.due_date.asc(), PlannedBill.name.asc()).all():
        amount = int(bill.amount_cents or 0)
        total += amount
        bills.append(
            {
                "id": str(bill.id),
                "name": bill.name,
                "amount_cents": amount,
                "due_date": bill.due_date.isoformat() if bill.due_date else None,
                "frequency": bill.frequency,
                "origin": bill.origin,
            }
        )
    return total, bills


def build_safe_to_spend_payload(inputs: SafeToSpendInputs | None = None) -> dict:
    """Build the dashboard safe-to-spend decision payload.

    Args:
        inputs: Optional normalized request inputs controlling user scope,
            horizon mode, effective date, and protected buffer.

    Returns:
        dict: API-serializable decision payload with component math and rationale.
    """

    inputs = inputs or SafeToSpendInputs()
    mode = _normalize_mode(inputs.mode)
    as_of = _coerce_date(inputs.as_of)
    buffer_cents = max(int(inputs.buffer_cents or 0), 0)
    accounts = _visible_accounts(inputs.user_id)
    spendable_cash_cents, account_payload, cash_coverage = _cash_account_payload(accounts)
    payday = _payday_prediction(as_of, inputs.user_id)
    next_income = date.fromisoformat(payday["next_payday"]) if payday["next_payday"] else None
    validated_payday = next_income if payday["next_payday"] else None
    windows = _windows(mode, as_of, validated_payday)
    protection_end = windows["protection_end"]
    display_end = windows["display_end"]
    upcoming_outflows_cents, bills = _upcoming_bill_payload(as_of, protection_end, inputs.user_id)
    spent_today_cents = _spent_between(as_of, as_of, inputs.user_id)
    pending_outflow_cents = _spent_between(as_of, as_of, inputs.user_id, pending=True)

    raw_amount = spendable_cash_cents - upcoming_outflows_cents - buffer_cents
    total_protected_room_cents = max(raw_amount, 0)
    protection_days = (protection_end - as_of).days + 1
    display_days = (display_end - as_of).days + 1
    # One protection-aware daily allowance for every mode: switching Today/Week/Payday never inflates it.
    daily_allowance_cents = total_protected_room_cents // protection_days
    per_day_cents = daily_allowance_cents
    amount_cents = daily_allowance_cents

    if raw_amount <= 0:
        status = "do_not_spend"
        message = "Hold discretionary spending until cash, bills, or buffer assumptions improve."
    elif per_day_cents < 2_500:
        status = "tight"
        message = f"Keep discretionary spending under ${per_day_cents / 100:,.0f} per day through {protection_end}."
    elif per_day_cents < 7_500:
        status = "caution"
        message = (
            f"You have about ${per_day_cents / 100:,.0f} per day through {protection_end} after known bills and buffer."
        )
    else:
        status = "comfortable"
        message = (
            f"You have about ${per_day_cents / 100:,.0f} per day through {protection_end} after known bills and buffer."
        )

    obligation_coverage = {
        "source": "planned_bills",
        "recurring_projected": False,
        "complete": False,
        "bill_count": len(bills),
        "through": protection_end.isoformat(),
    }
    warnings = []
    if not account_payload:
        warnings.append("No eligible cash accounts were found.")
    if cash_coverage["availability_unverified"]:
        warnings.append("Available balance is not reported for some accounts; current balance is used.")
    if cash_coverage["stale_balances"] or cash_coverage["unknown_freshness"]:
        warnings.append("Some balances are stale or have an unknown age.")
    if cash_coverage["deficit_accounts"]:
        warnings.append("An account is overdrawn; its deficit is deducted from your other cash.")
    if windows["awaiting_payday_post"]:
        warnings.append("Payday is today but has not posted; it is not counted as cash.")
    elif validated_payday is None:
        warnings.append("No validated payday; protecting a 14-day fallback window.")
    elif payday.get("needs_review"):
        warnings.append("Payday is inferred from past deposits, not confirmed.")
    if not obligation_coverage["complete"]:
        warnings.append("Recurring obligations are not projected yet; only planned bills are reserved.")

    # ``status`` is tightness; ``confidence`` is evidence completeness and needs every warning cleared.
    confidence = "limited" if not account_payload else ("estimated" if warnings else "ready")

    return {
        # ``amount_cents`` and ``per_day_cents`` are the daily allowance; ``total_horizon_cents`` and
        # ``total_protected_room_cents`` are all discretionary cash through the protection end.
        "amount_cents": amount_cents,
        "daily_allowance_cents": daily_allowance_cents,
        "total_horizon_cents": total_protected_room_cents,
        "total_protected_room_cents": total_protected_room_cents,
        "display_window_allowance_cents": daily_allowance_cents * display_days,
        "per_day_cents": per_day_cents,
        "calculation_version": CALCULATION_VERSION,
        "display_window": _window_payload(as_of, display_end),
        "protection_window": _window_payload(
            as_of,
            protection_end,
            basis=windows["basis"],
            payday_verified=validated_payday is not None and not windows["awaiting_payday_post"],
        ),
        "awaiting_payday_post": windows["awaiting_payday_post"],
        "default_buffer_cents": DEFAULT_BUFFER_CENTS,
        "obligation_coverage": obligation_coverage,
        "warnings": warnings,
        "status": status,
        "currency": "USD",
        "mode": mode,
        "as_of": as_of.isoformat(),
        "horizon_end": protection_end.isoformat(),
        "next_income_date": next_income.isoformat() if next_income else None,
        "payday_prediction": {k: v for k, v in payday.items() if k != "candidates"},
        "confidence": confidence,
        "components": {
            "spendable_cash_cents": spendable_cash_cents,
            "upcoming_outflows_cents": upcoming_outflows_cents,
            "required_buffer_cents": buffer_cents,
            "spent_today_cents": spent_today_cents,
            # Balances already include posted activity; it is shown for history, never deducted twice.
            "spent_today_included_in_balance": "unknown",
            "pending_cash_outflow_cents": pending_outflow_cents,
        },
        "accounts": account_payload,
        "opening_cash_sources": account_payload,
        "cash_coverage": cash_coverage,
        "upcoming_bills": bills,
        "message": message,
    }
