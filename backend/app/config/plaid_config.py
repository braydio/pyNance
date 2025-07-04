# backend/app/config/plaid_config.py


from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.configuration import Configuration

from .environment import PLAID_CLIENT_ID, PLAID_ENV, PLAID_SECRET

# Dynamically set base URL based on PLAID_ENV
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

configuration = Configuration(
    host=PLAID_BASE_URL, api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET}
)

api_client = ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)
