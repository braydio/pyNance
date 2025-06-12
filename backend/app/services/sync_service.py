import logging

from app.helpers.plaid_helpers import get_accounts as get_plaid_accounts
from app.helpers.teller_helpers import get_teller_accounts
from app.models import Account

logger = logging.getLogger(__name__)


def sync_account(account: Account) -> None:
    """
    Sync a single account by determining its provider and invoking the appropriate helper.
    Explicitly logs and forwards user_id and account_id to data capture functions.
    """
    provider = account.link_type.lower() if account.link_type else None
    user_id = account.user_id

    access_token = None
    if provider == "teller":
        if account.teller_account:
            access_token = account.teller_account.access_token
        else:
            logger.warning(f"Missing TellerAccount relation for account {account.id}")
    elif provider == "plaid":
        if account.plaid_account:
            access_token = account.plaid_account.access_token
        else:
            logger.warning(f"Missing PlaidAccount relation for account {account.id}")

    if not provider or not access_token or not user_id:
        logger.warning(
            f"Missing sync data for account {account.id} | provider={provider}"
        )
        return

    try:
        if provider == "teller":
            logger.info(
                f"[SYNC] Teller sync start: account={account.id}, user={user_id}"
            )
            get_teller_accounts(access_token, user_id)

        elif provider == "plaid":
            logger.info(
                f"[SYNC] Plaid sync start: account={account.id}, user={user_id}"
            )
            get_plaid_accounts(access_token, user_id)

        else:
            logger.warning(f"Unknown provider '{provider}' for account {account.id}")

    except Exception as e:
        logger.error(f"Sync error for account {account.id} ({provider}): {e}")
