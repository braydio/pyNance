
import logging
from backend.app.models import Account
from backend.app.helpers.teller_helpers import get_teller_accounts
from backend.app.helpers.plaid_helpers import get_accounts as get_plaid_accounts

logger = logging.getLogger(__name__)

def sync_account(account: Account) -> None:
    """
    Sync a single account by determining its provider and invoking the appropriate helper.
    Explicitly logs and forwards user_id and account_id to data capture functions.
    """
    provider = account.provider.lower() if account.provider else None
    user_id = account.user_id
    access_token = account.access_token

    if not provider or not access_token or not user_id:
        logger.warning(f"Missing sync data for account {account.id} | provider={provider}")
        return

    try:
        if provider == "teller":
            logger.info(f"[SYNC] Teller sync start: account={account.id}, user={user_id}")
            get_teller_accounts(access_token, user_id)

        elif provider == "plaid":
            logger.info(f"[SYNC] Plaid sync start: account={account.id}, user={user_id}")
            get_plaid_accounts(access_token, user_id)

        else:
            logger.warning(f"Unknown provider '{provider}' for account {account.id}")

    except Exception as e:
        logger.error(f"Sync error for account {account.id} ({provider}): {e}")

