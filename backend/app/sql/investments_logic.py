"""Helpers for storing and retrieving investment data."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from app.extensions import db
from app.models import (
    Account,
    InvestmentHolding,
    InvestmentTransaction,
    PlaidAccount,
    Security,
)


def get_investment_accounts() -> List[Dict[str, object]]:
    """Return accounts linked for Plaid investments."""
    query = Account.query.join(
        PlaidAccount, Account.account_id == PlaidAccount.account_id
    ).filter(PlaidAccount.product == "investments")
    accounts = []
    for acc in query.all():
        accounts.append(
            {
                "account_id": acc.account_id,
                "user_id": acc.user_id,
                "name": acc.name,
                "balance": acc.balance,
                "institution_name": acc.institution_name,
            }
        )
    return accounts


def upsert_investments_from_plaid(user_id: str, access_token: str) -> dict:
    """Fetch investments via Plaid and persist securities, holdings.

    Returns a summary dict with counts for upserts.
    """
    from app.helpers.plaid_helpers import get_investments

    data = get_investments(access_token) or {}
    secs = data.get("securities", []) or []
    holds = data.get("holdings", []) or []

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

    sec_upserts = 0
    for s in secs:
        # Map Plaid security fields sensibly
        security = Security(
            security_id=s.get("security_id"),
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

    holding_upserts = 0
    # Prefetch existing holdings for involved accounts to avoid duplicate inserts within this batch
    account_ids = list({h.get("account_id") for h in holds if h.get("account_id")})
    existing_rows = []
    if account_ids:
        existing_rows = InvestmentHolding.query.filter(
            InvestmentHolding.account_id.in_(account_ids)
        ).all()
    existing_map: Dict[tuple[str, str], InvestmentHolding] = {
        (row.account_id, row.security_id): row
        for row in existing_rows
        if row.security_id
    }

    for h in holds:
        acct_id = h.get("account_id")
        sec_id = h.get("security_id")
        if not acct_id or not sec_id:
            continue
        key = (acct_id, sec_id)
        obj = existing_map.get(key)
        if obj is None:
            obj = InvestmentHolding(
                account_id=acct_id,
                security_id=sec_id,
            )
            db.session.add(obj)
            existing_map[key] = obj  # prevent duplicate add within the same session

        # Update fields
        obj.quantity = h.get("quantity")
        obj.cost_basis = h.get("cost_basis")
        obj.institution_value = h.get("institution_value")
        obj.as_of = h.get("institution_price_as_of")
        obj.raw = _json_safe(h)
        holding_upserts += 1

    db.session.commit()
    return {
        "securities": sec_upserts,
        "holdings": holding_upserts,
    }


def upsert_investment_transactions(items: List[dict]) -> int:
    """Upsert a list of Plaid investment transactions.

    Returns the number of transactions processed.
    """
    count = 0
    for t in items or []:
        tx = InvestmentTransaction(
            investment_transaction_id=t.get("investment_transaction_id")
            or t.get("investment_transaction_id"),
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
    db.session.commit()
    return count
