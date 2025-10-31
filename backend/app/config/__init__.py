# backend/app/config/__init__.py

"""Expose configuration constants and logger setup across the app."""

from .constants import DATABASE_NAME, FILES, SQLALCHEMY_DATABASE_URI
from .environment import (
    ARBIT_EXPORTER_URL,
    BACKEND_PUBLIC_URL,
    CLIENT_NAME,
    ENABLE_ARBIT_DASHBOARD,
    FLASK_ENV,
    PLAID_CLIENT_ID,
    PLAID_CLIENT_NAME,
    PLAID_ENV,
    PLAID_SECRET,
    PLAID_WEBHOOK_SECRET,
    PRODUCTS,
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
    "PLAID_WEBHOOK_SECRET",
    "ENABLE_ARBIT_DASHBOARD",
    "ARBIT_EXPORTER_URL",
    "BACKEND_PUBLIC_URL",
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
    logger.debug(
        "Plaid client initialized for %s environment.", env_check
    )

logger.debug("Running in %s environment.", FLASK_ENV)
logger.debug("Loaded config from %s", __name__)
logger.debug("Initialized main database as %s", DATABASE_NAME)
logger.debug("SQLAlchemy Database URI: %s", SQLALCHEMY_DATABASE_URI)
if DATABASE_NAME:
    logger.debug("Connected database: %s", DATABASE_NAME)
logger.debug("Starting dashboard in Plaid %s Environment.", PLAID_ENV)
logger.debug(
    "Base URLs: \n\nPlaid: %s \nArbit: %s\n\n",
    PLAID_BASE_URL,
    ARBIT_EXPORTER_URL,
)
