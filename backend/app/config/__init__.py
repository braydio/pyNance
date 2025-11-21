# backend/app/config/__init__.py

"""Expose configuration constants and logger setup across the app.

The module emits a single INFO-level summary on import while deferring verbose
environment details to DEBUG logs so deployments can tune visibility via
``LOG_LEVEL`` without exposing sensitive configuration values such as full
database URIs or secrets.
"""

import logging

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

logger = setup_logger()

logger.info(
    "Configuration loaded (env=%s, plaid_env=%s, dashboard_enabled=%s, log_level=%s)",
    FLASK_ENV,
    PLAID_ENV,
    ENABLE_ARBIT_DASHBOARD,
    logging.getLevelName(logger.level),
)

if logger.isEnabledFor(logging.DEBUG):
    debug_context = {
        "plaid_client_initialized": bool(plaid_client),
        "flask_env": FLASK_ENV,
        "plaid_env": PLAID_ENV,
        "database_name": DATABASE_NAME,
        "dashboard_enabled": ENABLE_ARBIT_DASHBOARD,
        "plaid_base_url": PLAID_BASE_URL,
        "arbit_exporter_url": ARBIT_EXPORTER_URL,
        "directories": DIRECTORIES,
        "products": PRODUCTS,
    }
    logger.debug("Configuration context: %s", debug_context)
