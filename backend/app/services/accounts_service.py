"""Service helpers for account refresh operations."""

from app.helpers.plaid_helpers import get_accounts as _get_plaid_accounts


def fetch_accounts(access_token: str, user_id: str):
    """Fetch Plaid accounts for a user and update local history."""

    return _get_plaid_accounts(access_token, user_id)
