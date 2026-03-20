"""Helpers for storing and retrieving investment data."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.config import logger
from app.extensions import db
from app.models import (
    Account,
    InvestmentHolding,
    InvestmentTransaction,
    PlaidAccount,
    Security,
)


def _json_safe(obj: Any) -> Any:
    """Recursively convert Plaid SDK objects to JSON-safe primitives.

    - datetime/date -> ISO string
    - Decimal -> float
    - lists/dicts -> mapped recursively
    """

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


def _as_date(value: Any) -> date | None:
    """Return a ``date`` instance for supported Plaid date values.

    Args:
        value: Raw Plaid field value that may already be a ``date``/``datetime``
            object or an ISO-style string.

    Returns:
        Parsed ``date`` when coercion succeeds, otherwise ``None``.
    """

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
    return None


def get_investment_accounts(user_id: Optional[str] = None) -> List[Dict[str, object]]:
    """Return accounts linked for Plaid investments within an optional user scope.

    Args:
        user_id: Optional user identifier used to constrain account visibility.

    Returns:
        Serialized investment account records eligible for the investments APIs.
    """
    query = Account.query.join(PlaidAccount, Account.account_id == PlaidAccount.account_id).filter(
        Account.is_investment.is_(True)
    )
    if user_id:
        query = query.filter(Account.user_id == user_id)
    query = query.filter(PlaidAccount.product.ilike("%investments%"))
    accounts = []
    for acc in query.all():
        accounts.append(
            {
                "account_id": acc.account_id,
                "user_id": acc.user_id,
                "name": acc.name,
                "display_name": acc.display_name,
                "balance": float(acc.balance) if acc.balance is not None else None,
                "institution_name": acc.institution_name,
                "type": acc.account_type,
                "account_type": acc.account_type,
                "is_investment": bool(acc.is_investment),
                "investment_has_holdings": bool(acc.investment_has_holdings),
                "investment_has_transactions": bool(acc.investment_has_transactions),
                "product_provenance": acc.product_provenance,
            }
        )
    return accounts


def upsert_investment_holdings(
    securities: List[dict],
    holdings: List[dict],
    *,
    commit: bool = True,
) -> dict:
    """Persist investment securities and holdings.

    Args:
        securities: Plaid securities payload.
        holdings: Plaid holdings payload.
        commit: When ``True``, commit or roll back inside this helper. Callers
            that need a wider transaction boundary should pass ``False`` and
            manage the session themselves.

    Returns:
        Summary counts for persisted securities and holdings.
    """

    try:
        security_ids = set()
        sec_upserts = 0
        for s in securities or []:
            security_id = s.get("security_id")
            if not security_id:
                continue
            security_ids.add(security_id)
            # Map Plaid security fields sensibly
            security = Security(
                security_id=security_id,
                name=s.get("name"),
                ticker_symbol=s.get("ticker_symbol"),
                cusip=s.get("cusip"),
                isin=s.get("isin"),
                type=s.get("type"),
                is_cash_equivalent=s.get("is_cash_equivalent"),
                institution_price=s.get("institution_price"),
                institution_price_as_of=s.get("institution_price_as_of"),
                market_identifier_code=s.get("market_identifier_code"),
                iso_currency_code=s.get("iso_currency_code"),
                raw=_json_safe(s),
            )
            db.session.merge(security)
            sec_upserts += 1

        # Plaid should return matching security records for holdings, but when it
        # does not we still need a parent row before inserting the holding.
        for h in holdings or []:
            sec_id = h.get("security_id")
            if not sec_id or sec_id in security_ids:
                continue
            db.session.merge(
                Security(
                    security_id=sec_id,
                    name=h.get("name"),
                    ticker_symbol=h.get("ticker_symbol"),
                    iso_currency_code=h.get("iso_currency_code"),
                    raw={"placeholder_from_holding": True, "holding": _json_safe(h)},
                )
            )
            security_ids.add(sec_id)
            sec_upserts += 1

        # Flush parent security rows before issuing Core inserts for holdings.
        db.session.flush()

        # Conflict-safe upsert for holdings to avoid unique violations on
        # (account_id, security_id). Use PostgreSQL ON CONFLICT to update.
        from sqlalchemy.dialects.postgresql import insert

        holding_upserts = 0
        table = InvestmentHolding.__table__
        for h in holdings or []:
            acct_id = h.get("account_id")
            sec_id = h.get("security_id")
            if not acct_id or not sec_id:
                continue
            values = {
                "account_id": acct_id,
                "security_id": sec_id,
                "quantity": h.get("quantity"),
                "cost_basis": h.get("cost_basis"),
                "institution_value": h.get("institution_value"),
                # In holdings payloads, the date is often named institution_price_as_of
                "as_of": _as_date(h.get("institution_price_as_of") or h.get("as_of")),
                "raw": _json_safe(h),
            }
            stmt = insert(table).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[table.c.account_id, table.c.security_id],
                set_={
                    "quantity": stmt.excluded.quantity,
                    "cost_basis": stmt.excluded.cost_basis,
                    "institution_value": stmt.excluded.institution_value,
                    "as_of": stmt.excluded.as_of,
                    "raw": stmt.excluded.raw,
                },
            )
            db.session.execute(stmt)
            holding_upserts += 1

        if commit:
            db.session.commit()
        return {
            "securities": sec_upserts,
            "holdings": holding_upserts,
        }
    except Exception:
        if commit:
            db.session.rollback()
        logger.exception("Failed to upsert investments data from Plaid")
        raise


def upsert_investments_from_plaid(user_id: str, access_token: str, *, commit: bool = True) -> dict:
    """Fetch investments via Plaid and persist securities and holdings.

    Args:
        user_id: User identifier associated with the Plaid item. Present for
            caller symmetry and logging compatibility.
        access_token: Plaid access token for the investment item.
        commit: When ``True``, finalize the transaction inside this helper.

    Returns:
        Summary counts for persisted securities and holdings.
    """
    del user_id

    from app.helpers.plaid_helpers import get_investments

    data = get_investments(access_token) or {}
    return upsert_investment_holdings(
        data.get("securities", []) or [],
        data.get("holdings", []) or [],
        commit=commit,
    )


def upsert_investment_transactions(items: List[dict], *, commit: bool = True) -> int:
    """Upsert a list of Plaid investment transactions.

    Args:
        items: Plaid investment transaction payloads.
        commit: When ``True``, finalize the transaction inside this helper.

    Returns:
        The number of transactions processed.
    """
    try:
        count = 0
        for t in items or []:
            tx = InvestmentTransaction(
                investment_transaction_id=t.get("investment_transaction_id") or t.get("investment_transaction_id"),
                account_id=t.get("account_id"),
                security_id=t.get("security_id"),
                date=t.get("date"),
                amount=t.get("amount"),
                price=t.get("price"),
                quantity=t.get("quantity"),
                subtype=t.get("subtype"),
                type=t.get("type"),
                name=t.get("name"),
                fees=t.get("fees"),
                iso_currency_code=t.get("iso_currency_code"),
                raw=_json_safe(t),
            )
            db.session.merge(tx)
            count += 1
        if commit:
            db.session.commit()
        return count
    except Exception:
        if commit:
            db.session.rollback()
        logger.exception("Failed to upsert investment transactions")
        raise


def sync_investments_from_plaid(
    user_id: str,
    access_token: str,
    start_date: str,
    end_date: str,
    *,
    commit: bool = True,
) -> dict:
    """Fetch and persist Plaid securities, holdings, and transactions atomically.

    This helper orchestrates the entire Plaid investments refresh so callers can
    wrap all writes in a single transaction boundary.

    Args:
        user_id: User identifier associated with the Plaid item.
        access_token: Plaid access token used for both holdings and transactions.
        start_date: Inclusive start date for investment transactions.
        end_date: Inclusive end date for investment transactions.
        commit: When ``True``, commit or roll back inside this helper. Route and
            service callers should usually pass ``False`` so they can control the
            transaction boundary explicitly.

    Returns:
        Summary counts for securities, holdings, and investment transactions.
    """
    del user_id

    from app.helpers.plaid_helpers import get_investment_transactions, get_investments

    try:
        data = get_investments(access_token) or {}
        summary = upsert_investment_holdings(
            data.get("securities", []) or [],
            data.get("holdings", []) or [],
            commit=False,
        )
        transactions = get_investment_transactions(access_token, start_date, end_date)
        transaction_count = upsert_investment_transactions(transactions, commit=False)
        result = {
            **summary,
            "investment_transactions": transaction_count,
        }
        if commit:
            db.session.commit()
        return result
    except Exception:
        if commit:
            db.session.rollback()
        logger.exception("Failed to synchronize Plaid investments data")
        raise
