from app.providers import plaid


def sync_transactions(provider: str, account_id: str):
    if provider == "plaid":
        return plaid.sync_transactions(account_id)

    raise ValueError(f"Unsupported provider: {provider}")
