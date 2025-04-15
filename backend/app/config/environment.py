# backend/app/config/environment.py

import os
from dotenv import load_dotenv

load_dotenv()

VARIABLE_ENV_TOKEN = os.getenv("VARIABLE_ENV_TOKEN")
VARIABLE_ENV_ID = os.getenv("VARIABLE_ENV_ID")
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PLAID_CLIENT_NAME = os.getenv("PLAID_CLIENT_NAME")
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

TELLER_APP_ID = os.getenv("TELLER_APP_ID")
TELLER_API_BASE_URL = "https://api.teller.io"
