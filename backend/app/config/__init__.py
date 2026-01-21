"""
Expose configuration constants and logger setup across the app.

This module emits a single INFO-level summary on import while deferring
verbose configuration details to DEBUG logs. It intentionally avoids
Flask-specific environment variables and relies solely on ENV.
"""

import logging

from .constants import (
    DATABASE_NAME,
    DB_IDENTITY,
    FILES,
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_ENGINE_OPTIONS,
)
from .environment import (
    ARBIT_EXPORTER_URL,
    BACKEND_PUBLIC_URL,
    CLIENT_NAME,
    DB_SCHEMA,
    ENABLE_ARBIT_DASHBOARD,
    ENV,
    IS_DEV,
    IS_TEST,
    PLAID_CLIENT_ID,
    PLAID_CLIENT_NAME,
    PLAID_ENV,
    PLAID_SECRET,
    PLAID_WEBHOOK_SECRET,
    PRODUCTS,
)
from .log_setup import LOG_LEVEL, setup_logger
from .paths import DIRECTORIES
from .plaid_config import PLAID_BASE_URL, plaid_client

__all__ = [
    # environment
    "ENV",
    "DB_SCHEMA",
    "IS_DEV",
    "IS_TEST",
    # database
    "DATABASE_NAME",
    "SQLALCHEMY_DATABASE_URI",
    "SQLALCHEMY_ENGINE_OPTIONS",
    "DB_IDENTITY",
    # app / feature flags
    "CLIENT_NAME",
    "ENABLE_ARBIT_DASHBOARD",
    "ARBIT_EXPORTER_URL",
    "BACKEND_PUBLIC_URL",
    # plaid
    "PLAID_CLIENT_NAME",
    "PLAID_CLIENT_ID",
    "PLAID_SECRET",
    "PLAID_ENV",
    "PLAID_WEBHOOK_SECRET",
    "PLAID_BASE_URL",
    "plaid_client",
    "PRODUCTS",
    # misc
    "FILES",
    "DIRECTORIES",
    # logging
    "logger",
]

# initialize logger once
logger = setup_logger()

# concise startup summary (INFO-safe)
logger.info(
    f"Configuration loaded "
    f"(env={ENV}, "
    f"schema={DB_SCHEMA}, "
    f"plaid_env={PLAID_ENV}, "
    f"dashboard_enabled={ENABLE_ARBIT_DASHBOARD}, "
    f"log_level={LOG_LEVEL})"
)

# verbose diagnostics (DEBUG only)
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(
        "Configuration context: %s",
        {
            "database_name": DATABASE_NAME,
            "db_identity": DB_IDENTITY,
            "plaid_client_initialized": bool(plaid_client),
            "plaid_base_url": PLAID_BASE_URL,
            "arbit_exporter_url": ARBIT_EXPORTER_URL,
            "directories": DIRECTORIES,
            "products": PRODUCTS,
        },
    )
