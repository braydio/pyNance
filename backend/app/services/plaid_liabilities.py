"""Optional Plaid Liabilities enrichment (APR buckets and payment metadata).

One authorized ``/liabilities/get`` per Item, only when the Item's persisted scopes already
include ``liabilities``. The data is cached provider data, not real-time, and is never
fabricated: absent fields stay ``None`` and an empty APR list is not a 0% rate.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from app.config import logger
from app.extensions import db
from app.models import Account, PlaidAccount
from app.services.account_interest_rates import apply_apr, is_credit_card_account

LIABILITIES_PRODUCT = "liabilities"
# Errors meaning "this Item cannot supply liabilities" (not a transient failure).
UNAVAILABLE_ERROR_CODES = {
    "PRODUCTS_NOT_SUPPORTED",
    "PRODUCT_NOT_ENABLED",
    "ADDITIONAL_CONSENT_REQUIRED",
    "NO_LIABILITY_ACCOUNTS",
    "INVALID_PRODUCT",
}
_APR_TYPE_BUCKETS = {
    "purchase_apr": "purchase_apr",
    "cash_apr": "cash_apr",
    "balance_transfer_apr": "balance_transfer_apr",
    "penalty_apr": "penalty_apr",
    "special": "special",
}


def has_liabilities_scope(products) -> bool:
    """True when the persisted product scopes include liabilities."""

    return LIABILITIES_PRODUCT in set(products or ())


def _num(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def parse_liabilities(payload: dict) -> dict[str, dict]:
    """Normalize a ``/liabilities/get`` ``liabilities`` object keyed by ``account_id``.

    Credit cards keep every APR bucket separately (penalty and cash APR are never
    collapsed into purchase APR). Loans keep their fixed/variable rate apart from card APRs.
    Unknown product shapes are ignored.
    """

    liabilities = (payload or {}).get("liabilities") or {}
    parsed: dict[str, dict] = {}

    for card in liabilities.get("credit") or []:
        account_id = card.get("account_id")
        if not account_id:
            continue
        buckets: dict[str, Any] = {}
        for apr in card.get("aprs") or []:
            bucket = _APR_TYPE_BUCKETS.get(_enum_value(apr.get("apr_type")) or "", "special")
            entry = {
                "apr_percentage": _num(apr.get("apr_percentage")),
                "balance_subject_to_apr": _num(apr.get("balance_subject_to_apr")),
                "interest_charge_amount": _num(apr.get("interest_charge_amount")),
            }
            if entry["apr_percentage"] is None:
                continue
            if bucket == "special":
                buckets.setdefault("special", []).append(entry)
            else:
                buckets.setdefault(bucket, []).append(entry)
        parsed[account_id] = {
            "kind": "credit",
            "buckets": buckets,
            "minimum_payment_amount": _num(card.get("minimum_payment_amount")),
            "next_payment_due_date": _date(card.get("next_payment_due_date")),
            "statement_balance": _num(card.get("last_statement_balance")),
            "statement_date": _date(card.get("last_statement_issue_date")),
            "is_overdue": card.get("is_overdue"),
        }

    for loan in liabilities.get("student") or []:
        account_id = loan.get("account_id")
        if account_id:
            rate = _num(loan.get("interest_rate_percentage"))
            parsed[account_id] = {
                "kind": "loan",
                "buckets": {"loan_interest_rate": {"percentage": rate, "type": None}} if rate is not None else {},
                "minimum_payment_amount": _num(loan.get("minimum_payment_amount")),
                "next_payment_due_date": _date(loan.get("next_payment_due_date")),
                "statement_balance": None,
                "statement_date": _date(loan.get("last_statement_issue_date")),
            }

    for loan in liabilities.get("mortgage") or []:
        account_id = loan.get("account_id")
        if account_id:
            rate = loan.get("interest_rate") or {}
            pct = _num(rate.get("percentage"))
            parsed[account_id] = {
                "kind": "loan",
                "buckets": (
                    {"loan_interest_rate": {"percentage": pct, "type": _enum_value(rate.get("type"))}}
                    if pct is not None
                    else {}
                ),
                "minimum_payment_amount": _num(loan.get("next_monthly_payment")),
                "next_payment_due_date": _date(loan.get("next_payment_due_date")),
                "statement_balance": None,
                "statement_date": None,
            }
    return parsed


def request_liabilities(access_token: str) -> dict:
    """Perform the single ``/liabilities/get`` call for an Item and return it as a dict."""

    from plaid.model.liabilities_get_request import LiabilitiesGetRequest

    from app.config import plaid_client

    response = plaid_client.liabilities_get(LiabilitiesGetRequest(access_token=access_token))
    return response.to_dict() if hasattr(response, "to_dict") else dict(response)


def _item_accounts(item_id: str) -> list[Account]:
    return (
        Account.query.join(PlaidAccount, PlaidAccount.account_id == Account.account_id)
        .filter(PlaidAccount.item_id == item_id)
        .all()
    )


def _mark_unavailable(accounts: list[Account]) -> None:
    """Flag rate metadata as stale (older data kept) or unavailable (never fetched)."""

    for account in accounts:
        if is_credit_or_loan(account):
            account.liabilities_status = "stale" if account.liabilities_as_of else "unavailable"


def is_credit_or_loan(account: Account) -> bool:
    kind = (account.type or "").lower()
    return is_credit_card_account(account) or kind in {"loan", "liability"}


def apply_liabilities(
    item_accounts: list[Account], parsed: dict[str, dict], *, now: datetime, owner_user_id: str | None = None
) -> dict:
    """Persist parsed liabilities onto the Item's own accounts.

    Response accounts that are not owned by this Item (or by the same user) are rejected.
    """

    by_id = {account.account_id: account for account in item_accounts}
    updated, rejected = [], []

    for account_id, info in parsed.items():
        account = by_id.get(account_id)
        if account is None or (owner_user_id and account.user_id and account.user_id != owner_user_id):
            rejected.append(account_id)
            continue
        buckets = info["buckets"]
        account.apr_details = buckets or None
        account.minimum_payment_amount = _dec(info["minimum_payment_amount"])
        account.next_payment_due_date = info["next_payment_due_date"]
        account.statement_balance = _dec(info["statement_balance"])
        account.statement_date = info["statement_date"]
        account.liabilities_as_of = now
        account.liabilities_status = "ok" if buckets else "no_rates_reported"

        purchase = [e["apr_percentage"] for e in buckets.get("purchase_apr", [])] if info["kind"] == "credit" else []
        if len(set(purchase)) == 1:  # a single genuine purchase APR; ambiguity stays in apr_details
            apply_apr(account, purchase[0], "provider", as_of=now, details=buckets, confidence="high")
        updated.append(account_id)

    missing = [a for a in by_id.values() if a.account_id not in parsed and is_credit_or_loan(a)]
    for account in missing:
        account.liabilities_status = "no_rates_reported"
    return {"updated": updated, "rejected": rejected}


def _dec(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value)).quantize(Decimal("0.01"))


def refresh_item_liabilities(
    item_id: str, access_token: str, *, products, now: datetime | None = None, owner_user_id: str | None = None
) -> dict:
    """Fetch and store liabilities for every account on ``item_id`` with one remote call.

    Returns ``{"status": "skipped"|"ok"|"unavailable"|"error", ...}``. Never raises for
    provider errors; ``reauth`` is set when the Item needs Link update mode.
    """

    if not has_liabilities_scope(products):
        return {"status": "skipped", "reason": "scope_not_enabled"}
    now = now or datetime.now(timezone.utc)
    accounts = _item_accounts(item_id)
    try:
        payload = request_liabilities(access_token)
    except Exception as exc:  # provider/network failure must not abort the refresh loop
        from app.helpers.plaid_helpers import extract_plaid_error_payload

        error = extract_plaid_error_payload(exc)
        code = error.get("plaid_error_code")
        if code in UNAVAILABLE_ERROR_CODES:
            _mark_unavailable(accounts)
            return {"status": "unavailable", "error": error}
        logger.warning("Plaid liabilities refresh failed for item %s: %s", item_id, code or type(exc).__name__)
        _mark_unavailable(accounts)
        return {"status": "error", "error": error, "reauth": code == "ITEM_LOGIN_REQUIRED"}

    result = apply_liabilities(accounts, parse_liabilities(payload), now=now, owner_user_id=owner_user_id)
    db.session.commit()
    return {"status": "ok", **result}
