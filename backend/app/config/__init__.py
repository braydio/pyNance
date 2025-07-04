# backend/app/config/__init__.py

"""Expose configuration constants and logger setup across the app."""

from .constants import DATABASE_NAME, FILES, SQLALCHEMY_DATABASE_URI
from .environment import (
    CLIENT_NAME,
    FLASK_ENV,
    PLAID_CLIENT_ID,
    PLAID_CLIENT_NAME,
    PLAID_ENV,
    PLAID_SECRET,
    PRODUCTS,
    TELLER_API_BASE_URL,
    TELLER_APP_ID,
    TELLER_CERTIFICATE,
    TELLER_PRIVATE_KEY,
    TELLER_WEBHOOK_SECRET,
    VARIABLE_ENV_ID,
    VARIABLE_ENV_TOKEN,
)
from .log_setup import setup_logger
from .paths import DIRECTORIES
from .plaid_config import PLAID_BASE_URL, plaid_client

__all__ = [
    "CLIENT_NAME",
    "FLASK_ENV",
    "PLAID_CLIENT_NAME",
    "PLAID_CLIENT_ID",
    "PLAID_SECRET",
    "PLAID_ENV",
    "TELLER_API_BASE_URL",
    "TELLER_APP_ID",
    "TELLER_CERTIFICATE",
    "TELLER_PRIVATE_KEY",
    "TELLER_WEBHOOK_SECRET",
    "VARIABLE_ENV_TOKEN",
    "VARIABLE_ENV_ID",
    "PRODUCTS",
    "FILES",
    "DATABASE_NAME",
    "SQLALCHEMY_DATABASE_URI",
    "DIRECTORIES",
    "plaid_client",
    "PLAID_BASE_URL",
    "logger",
]

env_check = PLAID_ENV.upper()

logger = setup_logger()

if plaid_client:
    logger.debug(f"Plaid client initialized for {env_check} environment.")

logger.debug(f"Running in {FLASK_ENV} environment.")
logger.debug(f"Loaded config from {__name__}")
logger.debug(f"Initialized main database as {DATABASE_NAME}")
logger.debug(f"SQLAlchemy Database URI: {SQLALCHEMY_DATABASE_URI}")
logger.debug(f"Starting dashboard in Plaid {PLAID_ENV} Environment.")
logger.debug(
    f"Base URLs: \n\nPlaid: {PLAID_BASE_URL} \nTeller: {TELLER_API_BASE_URL}\n\n"
)
