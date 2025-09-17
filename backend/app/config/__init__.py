# backend/app/config/__init__.py

"""Expose configuration constants and logger setup across the app."""

from .constants import (
    CURRENT_DATABASE_PATH,
    DATABASE_BACKUP_DIR,
    DATABASE_BACKUP_PATH,
    DATABASE_BASE_DIR,
    DATABASE_NAME,
    DATABASE_PATH,
    FILES,
    SQLALCHEMY_DATABASE_URI,
)
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
    "PLAID_WEBHOOK_SECRET",
    "ENABLE_ARBIT_DASHBOARD",
    "ARBIT_EXPORTER_URL",
    "BACKEND_PUBLIC_URL",
    "TELLER_API_BASE_URL",
    "TELLER_APP_ID",
    "TELLER_CERTIFICATE",
    "TELLER_PRIVATE_KEY",
    "TELLER_WEBHOOK_SECRET",
    "VARIABLE_ENV_TOKEN",
    "VARIABLE_ENV_ID",
    "PRODUCTS",
    "FILES",
    "DATABASE_BASE_DIR",
    "DATABASE_BACKUP_DIR",
    "DATABASE_BACKUP_PATH",
    "DATABASE_NAME",
    "DATABASE_PATH",
    "CURRENT_DATABASE_PATH",
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
logger.debug(f"Network database directory: {DATABASE_BASE_DIR}")
logger.debug(f"Network database path: {CURRENT_DATABASE_PATH}")
logger.debug(f"Local database backup directory: {DATABASE_BACKUP_DIR}")
logger.debug(f"Local database path: {DATABASE_PATH}")
logger.debug(f"Starting dashboard in Plaid {PLAID_ENV} Environment.")
logger.debug(
    f"Base URLs: \n\nPlaid: {PLAID_BASE_URL} \nTeller: {TELLER_API_BASE_URL} \nArbit: {ARBIT_EXPORTER_URL}\n\n"
)
