# backend/app/config/environment.py

import os

from dotenv import load_dotenv

from .paths import DIRECTORIES

load_dotenv()

# Dev Environment Check
FLASK_ENV = os.getenv("FLASK_ENV", "production")
CLIENT_NAME = os.getenv("CLIENT_NAME", "pyNance-Dash")

# Plaid client ID and API secret for authentication
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET_KEY")
PLAID_CLIENT_NAME = os.getenv("CLIENT_NAME")

# Misc Plaid environment setup
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

# Base URLs for  Teller API Endpoints
TELLER_API_BASE_URL = "https://api.teller.io"

# Teller application ID, certificates and API key for authentication
TELLER_APP_ID = os.getenv("TELLER_APP_ID")
TELLER_CERTIFICATE = DIRECTORIES["CERTS_DIR"] / "certificate.pem"
TELLER_PRIVATE_KEY = DIRECTORIES["CERTS_DIR"] / "private_key.pem"

# Webhook for product update notifications
TELLER_WEBHOOK_SECRET = os.getenv("TELLER_WEBHOOK_SECRET", "No Teller Webhook in .env")

# Misc. Dev. Variables for testing
VARIABLE_ENV_TOKEN = os.getenv("VARIABLE_ENV_TOKEN")
VARIABLE_ENV_ID = os.getenv("VARIABLE_ENV_ID")
