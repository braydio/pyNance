# backend/app/config/__init__.py

from .log_setup import setup_logger
from .plaid_config import PLAID_BASE_URL, plaid_client
from .environment import (
    CLIENT_NAME,
    FLASK_ENV,
    PLAID_CLIENT_NAME,
    PLAID_CLIENT_ID,
    PLAID_SECRET,
    PLAID_ENV,
    TELLER_API_BASE_URL,
    TELLER_APP_ID,
    TELLER_CERTIFICATE,
    TELLER_PRIVATE_KEY,
    TELLER_WEBHOOK_SECRET,
    VARIABLE_ENV_TOKEN,
    VARIABLE_ENV_ID,
    PRODUCTS,
)
from .constants import (
    FILES,
    TELEMETRY,
    DIRECTORIES,
    DATABASE_NAME,
    SQLALCHEMY_DATABASE_URI,
)
from .paths import BASE_DIR

env_check = PLAID_ENV.upper()

logger = setup_logger()

logger.debug(f"Running in {FLASK_ENV} environment.")
logger.debug(f"Loaded config from {__name__}")
logger.debug(f"Initialized main database as {DATABASE_NAME}")
logger.debug(f"SQLAlchemy Database URI: {SQLALCHEMY_DATABASE_URI}")
logger.debug(f"Starting dashboard in Plaid {PLAID_ENV} Environment.")
logger.debug(
    f"Base URLs: \n\nPlaid: {PLAID_BASE_URL} \nTeller: {TELLER_API_BASE_URL}\n\n"
)
