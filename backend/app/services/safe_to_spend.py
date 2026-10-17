"""Safe-to-spend dashboard decisioning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import and_, func, or_

from app.extensions import db
from app.models import Account, PlannedBill, PlanningScenario, Transaction
from app.utils.finance_utils import normalize_account_balance

TWOPLACES = Decimal("0.01")
DEFAULT_BUFFER_CENTS = 25_000
DEFAULT_MODE = "today"
MODE_WINDOWS = {
    "today": 0,
    "week": 6,
    "until_payday": 14,
}
CASH_ACCOUNT_TOKENS = {
    "cash",
    "checking",
    "savings",
    "depository",
    "prepaid",
    "money market",
    "money_market",
}


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


def _is_cash_account(account: Account) -> bool:
    """Return True when an account should count toward daily spendable cash."""

    if account.is_investment:
        return False
    fields = {str(account.type or "").lower(), str(account.subtype or "").lower(), str(account.name or "").lower()}
    return any(token in field for field in fields for token in CASH_ACCOUNT_TOKENS)


def _visible_accounts(user_id: str | None = None) -> list[Account]:
    """Load visible accounts, optionally scoped by user."""

    query = Account.query.filter(or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)))
    if user_id:
        query = query.filter(Account.user_id == user_id)
    return query.all()


def _cash_account_payload(accounts: list[Account]) -> tuple[int, list[dict]]:
    """Build spendable-cash cents and source account metadata."""

    total_cents = 0
    payload = []
    for account in accounts:
        if not _is_cash_account(account):
            continue
        normalized = normalize_account_balance(
            account.balance, account.type, account_id=account.account_id, subtype=account.subtype
        )
        balance_cents = max(_to_cents(normalized), 0)
        total_cents += balance_cents
        payload.append(
            {
                "account_id": account.account_id,
                "name": account.display_name,
                "type": account.type,
                "subtype": account.subtype,
                "balance_cents": balance_cents,
            }
        )
    return total_cents, payload


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


def _spent_between(start: date, end: date, user_id: str | None = None) -> int:
    """Return posted non-internal outflows between inclusive date boundaries."""

    query = (
        db.session.query(func.coalesce(func.sum(func.abs(Transaction.amount)), 0))
        .join(Account, Account.account_id == Transaction.account_id)
        .filter(or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)))
        .filter(Transaction.date >= start, Transaction.date <= end)
        .filter(_outflow_filter())
        .filter(or_(Transaction.is_internal.is_(False), Transaction.is_internal.is_(None)))
    )
    if user_id:
        query = query.filter(Account.user_id == user_id)
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


def _horizon_end(mode: str, as_of: date, next_income_date: date | None) -> date:
    """Resolve the inclusive planning horizon for the selected mode."""

    if mode == "until_payday" and next_income_date:
        return next_income_date
    return as_of + timedelta(days=MODE_WINDOWS[mode])


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
    spendable_cash_cents, account_payload = _cash_account_payload(accounts)
    payday = _payday_prediction(as_of, inputs.user_id)
    next_income = date.fromisoformat(payday["next_payday"]) if payday["next_payday"] else None
    horizon_end = _horizon_end(mode, as_of, next_income)
    upcoming_outflows_cents, bills = _upcoming_bill_payload(as_of, horizon_end, inputs.user_id)
    spent_today_cents = _spent_between(as_of, as_of, inputs.user_id)

    raw_amount = spendable_cash_cents - upcoming_outflows_cents - buffer_cents - spent_today_cents
    amount_cents = max(raw_amount, 0)
    days = max((horizon_end - as_of).days + 1, 1)
    per_day_cents = amount_cents // days

    if raw_amount <= 0:
        status = "do_not_spend"
        message = "Hold discretionary spending until cash, bills, or buffer assumptions improve."
    elif per_day_cents < 2_500:
        status = "tight"
        message = f"Keep discretionary spending under ${per_day_cents / 100:,.0f} per day for this horizon."
    elif per_day_cents < 7_500:
        status = "caution"
        message = f"You have about ${per_day_cents / 100:,.0f} per day after known bills and buffer."
    else:
        status = "comfortable"
        message = f"You have about ${per_day_cents / 100:,.0f} per day after known bills and buffer."

    confidence = "ready" if account_payload else "limited"
    if not bills:
        confidence = "estimated"

    return {
        "amount_cents": amount_cents if mode == "today" else per_day_cents,
        "total_horizon_cents": amount_cents,
        "per_day_cents": per_day_cents,
        "status": status,
        "currency": "USD",
        "mode": mode,
        "as_of": as_of.isoformat(),
        "horizon_end": horizon_end.isoformat(),
        "next_income_date": next_income.isoformat() if next_income else None,
        "payday_prediction": {k: v for k, v in payday.items() if k != "candidates"},
        "confidence": confidence,
        "components": {
            "spendable_cash_cents": spendable_cash_cents,
            "upcoming_outflows_cents": upcoming_outflows_cents,
            "required_buffer_cents": buffer_cents,
            "spent_today_cents": spent_today_cents,
        },
        "accounts": account_payload,
        "upcoming_bills": bills,
        "message": message,
    }
