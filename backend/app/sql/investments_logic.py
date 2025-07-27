"""Helpers for storing and retrieving investment data."""

from __future__ import annotations

from typing import Dict, List

from app.extensions import db
from app.models import Account, PlaidAccount


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
    """Placeholder for persisting Plaid investments data."""
    from app.helpers.plaid_helpers import get_investments

    holdings = get_investments(access_token)
    # TODO: persist holdings to models when schema is defined
    db.session.commit()
    return holdings
