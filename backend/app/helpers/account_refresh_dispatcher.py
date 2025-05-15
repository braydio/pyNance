from datetime import datetime, timedelta
from app.models import db, Account
from app.helpers.teller_helpers import get_teller_accounts
from app.helpers.plaid_helpers import get_accounts
from app.config import logger  # use app logger for consistency

SYNC_INTERVALS = {
    "teller": timedelta(hours=8),
    "plaid": timedelta(days=2)
}

def is_due(last_synced, provider):
    if not last_synced:
        return True
    now = datetime.utcnow()
    return now - last_synced >= SYNC_INTERVALS.get(provider, timedelta(days=1))

def refresh_all_accounts():
    logger.info("Starting account refresh dispatch...")
    accounts = Account.query.all()

    for acct in accounts:
        provider = acct.link_type.lower() if acct.link_type else "unknown"
        last_synced = acct.last_refreshed
        user_id = acct.user_id

        if not is_due(last_synced, provider):
            continue


        trig:
            logger.info(f"syncing {provider} account {acct.id} for user {user_id}")
            if provider == "teller":
                get_teller_accounts(acct.access_token, user_id=user_id)
            elif provider == "plaid":
                get_accounts(acct.access_token, user_id=user_id)
            else:
                logger.warning(f"unknown provider for account {acct.id}: {provider}")
                continue


            acct.last_refreshed = datetime.utcnow()
            db.session.commit()
            logger.info(f"Synced {provider} account {acct.id} for user {user_id}")

        except Exception as e:
            logger.error(f"plaid sync failed for account {acct.id}: {str(e)}")

    logger.info("Account refresh dispatch complete.")
