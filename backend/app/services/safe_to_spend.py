"""Safe-to-spend dashboard decisioning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, or_

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
INCOME_CATEGORY_TOKENS = {"income", "payroll", "paycheck", "wages", "salary"}


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
        normalized = normalize_account_balance(account.balance, account.type, account_id=account.account_id)
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


def _spent_between(start: date, end: date, user_id: str | None = None) -> int:
    """Return posted non-internal outflows between inclusive date boundaries."""

    query = (
        db.session.query(func.coalesce(func.sum(func.abs(Transaction.amount)), 0))
        .join(Account, Account.account_id == Transaction.account_id)
        .filter(or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)))
        .filter(Transaction.date >= start, Transaction.date <= end)
        .filter(Transaction.amount < 0)
        .filter(or_(Transaction.is_internal.is_(False), Transaction.is_internal.is_(None)))
    )
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    return _to_cents(query.scalar())


def _looks_like_income(transaction: Transaction) -> bool:
    """Return True when recent transaction metadata suggests wage income."""

    fields = [transaction.category, transaction.category_slug, transaction.category_display, transaction.description]
    pfc = transaction.personal_finance_category if isinstance(transaction.personal_finance_category, dict) else {}
    fields.extend([pfc.get("primary"), pfc.get("detailed")])
    haystack = " ".join(str(field or "").lower() for field in fields)
    return any(token in haystack for token in INCOME_CATEGORY_TOKENS)


def _next_income_date(as_of: date, user_id: str | None = None) -> date | None:
    """Infer the next payday from recent income cadence when possible."""

    lookback = as_of - timedelta(days=90)
    query = (
        Transaction.query.join(Account, Account.account_id == Transaction.account_id)
        .filter(or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)))
        .filter(Transaction.date >= lookback, Transaction.date <= as_of)
        .filter(Transaction.amount > 0)
        .order_by(Transaction.date.asc())
    )
    if user_id:
        query = query.filter(Transaction.user_id == user_id)

    income_dates = []
    for transaction in query.all():
        if _looks_like_income(transaction):
            raw_date = transaction.date.date() if isinstance(transaction.date, datetime) else transaction.date
            income_dates.append(raw_date)

    if len(income_dates) < 2:
        return None

    intervals = [
        (right - left).days for left, right in zip(income_dates, income_dates[1:]) if 1 <= (right - left).days <= 45
    ]
    if not intervals:
        return None
    cadence = round(sum(intervals) / len(intervals))
    next_date = income_dates[-1]
    while next_date <= as_of:
        next_date += timedelta(days=cadence)
    return next_date


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
    next_income = _next_income_date(as_of, inputs.user_id)
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
