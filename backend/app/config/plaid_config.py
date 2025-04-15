# backend/app/config/plaid_config.py

import os
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.api import plaid_api
from .environment import PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV, PLAID_BASE_URL

configuration = Configuration(
    host=PLAID_BASE_URL,
    api_key={
        "clientId": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET
    }
)

api_client = ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)
