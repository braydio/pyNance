from app.providers import plaid, teller


def sync_transactions(provider: str, account_id: str):
    if provider == "plaid":
        return plaid.sync_transactions(account_id)
    elif provider == "teller":
        return teller.sync_transactions(account_id)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
