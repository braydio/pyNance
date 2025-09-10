"""Helpers for storing and retrieving investment data."""

from __future__ import annotations

from typing import Dict, List, Tuple

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
            raw=s,
        )
        db.session.merge(security)
        sec_upserts += 1

    holding_upserts = 0
    for h in holds:
        holding = InvestmentHolding(
            account_id=h.get("account_id"),
            security_id=h.get("security_id"),
            quantity=h.get("quantity"),
            cost_basis=h.get("cost_basis"),
            institution_value=h.get("institution_value"),
            as_of=h.get("institution_price_as_of"),
            raw=h,
        )
        db.session.merge(holding)
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
            raw=t,
        )
        db.session.merge(tx)
        count += 1
    db.session.commit()
    return count
