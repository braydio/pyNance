# backend/app/config/environment.py

import os
from dotenv import load_dotenv
from .paths import DIRECTORIES

load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PLAID_CLIENT_NAME = os.getenv("PLAID_CLIENT_NAME")

PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")

PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"
TELLER_API_BASE_URL = "https://api.teller.io"

TELLER_APP_ID = os.getenv("TELLER_APP_ID")

TELLER_CERTIFICATE = DIRECTORIES["CERTS_DIR"] / "certificate.pem"
TELLER_PRIVATE_KEY = DIRECTORIES["CERTS_DIR"] / "private_key.pem"

VARIABLE_ENV_TOKEN = os.getenv("VARIABLE_ENV_TOKEN")
VARIABLE_ENV_ID = os.getenv("VARIABLE_ENV_ID")
