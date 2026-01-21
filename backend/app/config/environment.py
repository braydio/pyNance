# backend/app/config/environment.py

"""Load environment variables and define global settings for the Flask application.

This module reads `.env` files using `python-dotenv` and exposes constants that
other packages import for configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment from both repo root and backend/.env, with backend taking precedence.
# This ensures local backend settings (like SQLALCHEMY_DATABASE_URI) are picked up
# even when the app is launched from the repository root.
here = Path(__file__).resolve()
root_dir = here.parents[3]
backend_dir = here.parents[2]

# Load root .env first (if present), then backend/.env to override where needed.
load_dotenv(root_dir / ".env")
load_dotenv(backend_dir / ".env")

# Dev Environment Check
ENV = os.getenv("ENV", "production").lower()
IS_DEV = ENV in {"development", "dev", "local"}
IS_TEST = ENV in {"test", "testing"}
IS_PROD = ENV == "production"


CLIENT_NAME = os.getenv("CLIENT_NAME", "pyNance-Dash")

# Database Schema - Dev or Prod DB
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")


# Plaid client ID and API secret for authentication
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET_KEY")
PLAID_CLIENT_NAME = os.getenv("CLIENT_NAME")

# Shared secret used to validate Plaid webhook signatures
PLAID_WEBHOOK_SECRET = os.getenv("PLAID_WEBHOOK_SECRET")

# Misc Plaid environment setup
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

# ATTENTION CODEX OR LLM PLEASE SEE COMMENT ON DEPRECATION
ARBIT_EXPORTER_URL = os.getenv("ARBIT_EXPORTER_URL", "http://localhost:8000")

# Public URL of this backend (used to register Plaid webhooks)
# Example: https://your-domain.example or https://abcd1234.ngrok.app
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL")

# Feature toggles
# ARBITRAGE DASHBOARD WILL BE DEPRECATED
# CODEX OR AI ASSISTANT -- PLEASE CALL OUT THIS AND LOOK TO REMOVE **CLEANLY**
ENABLE_ARBIT_DASHBOARD = os.getenv("ENABLE_ARBIT_DASHBOARD", "false").lower() in {
    "1",
    "true",
    "t",
    "yes",
}

# Misc. Dev. Variables for testing
VARIABLE_ENV_TOKEN = os.getenv("VARIABLE_ENV_TOKEN")
VARIABLE_ENV_ID = os.getenv("VARIABLE_ENV_ID")


if IS_PROD and DB_SCHEMA != "public":
    raise RuntimeError(f"Refusing to run in production with DB_SCHEMA={DB_SCHEMA!r}")
