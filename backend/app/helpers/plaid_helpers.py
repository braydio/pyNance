import requests
from app.config import PLAID_BASE_URL, PLAID_CLIENT_ID, PLAID_SECRET, logger


def generate_link_token(user_id, products=["transactions"]):
    """
    Generate a Plaid link token for the given user and products.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "client_name": "pyNance",
        "products": products,
        "country_codes": ["US"],
        "language": "en",
        "user": {"client_user_id": user_id},
    }
    url = f"{PLAID_BASE_URL}/link/token/create"
    logger.debug(f"Generating Plaid link token with payload: {payload}")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("link_token")


def exchange_public_token(public_token):
    """
    Exchange a Plaid public token for an access token and item_id.
    Returns the full exchange response.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "public_token": public_token,
    }
    url = f"{PLAID_BASE_URL}/item/public_token/exchange"
    logger.debug("Exchanging Plaid public token for access token")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def get_accounts(access_token):
    """
    Retrieve accounts data from Plaid.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    url = f"{PLAID_BASE_URL}/accounts/get"
    logger.debug("Fetching Plaid accounts")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def get_transactions(access_token, start_date, end_date):
    """
    Retrieve transactions from Plaid for the given date range.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
        "start_date": start_date,
        "end_date": end_date,
    }
    url = f"{PLAID_BASE_URL}/transactions/get"
    logger.debug("Fetching Plaid transactions")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def get_investments(access_token):
    """
    Retrieve investments holdings from Plaid.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    url = f"{PLAID_BASE_URL}/investments/holdings/get"
    logger.debug("Fetching Plaid investments holdings")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()
