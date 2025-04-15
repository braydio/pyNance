
# backend/app/config/__init__.py

from .log_setup import setup_logger
from .plaid_config import plaid_client
from .environment import (
    PLAID_CLIENT_NAME, PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV, PLAID_BASE_URL,
    TELLER_API_BASE_URL, TELLER_APP_ID, VARIABLE_ENV_TOKEN, VARIABLE_ENV_ID, PRODUCTS
)
from .constants import FILES, TELEMETRY, DIRECTORIES, SQLALCHEMY_DATABASE_URI
from .paths import BASE_DIR

logger = setup_logger()
logger.debug(f"Loaded config from {__name__}")

