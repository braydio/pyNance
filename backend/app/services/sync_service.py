"""Helpers for kicking off Plaid account sync operations."""

import logging

from app.helpers.plaid_helpers import get_accounts as get_plaid_accounts
from app.models import Account

logger = logging.getLogger(__name__)


def sync_account(account: Account) -> None:
    """Trigger a Plaid sync for the provided account.

    Args:
        account: The account instance whose Plaid data should be refreshed.

    Accounts that are not Plaid-linked or are missing credentials are skipped
    with a warning to keep the dispatcher resilient.
    """

    provider = account.link_type.lower() if account.link_type else None
    if provider != "plaid":
        logger.warning(
            "Skipping sync for unsupported provider '%s' on account %s",
            provider,
            account.id,
        )
        return

    user_id = account.user_id
    plaid_account = account.plaid_account
    access_token = (
        getattr(plaid_account, "access_token", None) if plaid_account else None
    )

    if not user_id or not access_token:
        logger.warning(
            "Missing Plaid credentials for account %s | user_id=%s",
            account.id,
            user_id,
        )
        return

    try:
        logger.info(f"[SYNC] Plaid sync start: account={account.id}, user={user_id}")
        get_plaid_accounts(access_token, user_id)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Sync error for account %s (plaid): %s",
            account.id,
            exc,
        )
