# backend/app/config/environment.py

"""Load environment variables and define global settings for the Flask application.

This module reads `.env` files using `python-dotenv` and exposes constants that
other packages import for configuration."""

import os

from dotenv import load_dotenv

load_dotenv()

# Dev Environment Check
FLASK_ENV = os.getenv("FLASK_ENV", "production")
CLIENT_NAME = os.getenv("CLIENT_NAME", "pyNance-Dash")

# Plaid client ID and API secret for authentication
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET_KEY")
PLAID_CLIENT_NAME = os.getenv("CLIENT_NAME")

# Shared secret used to validate Plaid webhook signatures
PLAID_WEBHOOK_SECRET = os.getenv("PLAID_WEBHOOK_SECRET")

# Misc Plaid environment setup
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

# Base URL for Arbit metrics exporter
ARBIT_EXPORTER_URL = os.getenv("ARBIT_EXPORTER_URL", "http://localhost:8000")

# Public URL of this backend (used to register Plaid webhooks)
# Example: https://your-domain.example or https://abcd1234.ngrok.app
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL")

# Feature toggles
# Enable optional arbitrage dashboard
ENABLE_ARBIT_DASHBOARD = os.getenv("ENABLE_ARBIT_DASHBOARD", "false").lower() in {
    "1",
    "true",
    "t",
    "yes",
}

# Misc. Dev. Variables for testing
VARIABLE_ENV_TOKEN = os.getenv("VARIABLE_ENV_TOKEN")
VARIABLE_ENV_ID = os.getenv("VARIABLE_ENV_ID")
