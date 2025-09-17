# backend/app/config/constants.py

"""Centralized file paths and runtime constants for the Flask backend."""

import os
from pathlib import Path

from .environment import PLAID_ENV
from .paths import DIRECTORIES

FILES = {
    "LINKED_ACCOUNTS": DIRECTORIES["DATA_DIR"] / "LinkAccounts.json",
    "LINKED_ITEMS": DIRECTORIES["DATA_DIR"] / "LinkItems.json",
    "INVESTMENTS": DIRECTORIES["DATA_DIR"] / "LinkInvestments.json",
    "TRANSACTIONS": DIRECTORIES["DATA_DIR"] / "Transactions.json",
    "LAST_TX_REFRESH": DIRECTORIES["TEMP_DIR"] / "TxRefresh_Temporary.json",
    "TRANSACTIONS_EXPORT": DIRECTORIES["TEMP_DIR"] / "Transactions.json",
    "TRANSACTIONS_RAW_ENRICHED": DIRECTORIES["TEMP_DIR"]
    / "TransactionsRawEnriched.json",
    "DEFAULT_THEME": DIRECTORIES["THEMES_DIR"] / "default.css",
    "CURRENT_THEME": DIRECTORIES["THEMES_DIR"] / "current_theme.txt",
    "ARCHIVE_FILE": DIRECTORIES["ARCHIVE_DIR"] / "archive.json",
    "PLAID_TOKENS": DIRECTORIES["DATA_DIR"] / "PlaidTokens.json",
    "TELLER_TOKENS": DIRECTORIES["DATA_DIR"] / "TellerDotTokens.json",
    "TELLER_ACCOUNTS": DIRECTORIES["DATA_DIR"] / "TellerDotAccounts.json",
    "TELLER_DOT_CERT": DIRECTORIES["CERTS_DIR"] / "certificate.pem",
    "TELLER_DOT_KEY": DIRECTORIES["CERTS_DIR"] / "private_key.pem",
}

FRONTEND_DIST_DIR = os.path.join(os.path.dirname(__file__), "../../../frontend/dist")

# Allow overriding the database name via environment variable for demos/tests
DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "developing_dash.db" if PLAID_ENV == "sandbox" else "dashboard_database.db",
)

DATABASE_BACKUP_DIR = DIRECTORIES["DATA_DIR"]
DATABASE_BACKUP_PATH = DATABASE_BACKUP_DIR / DATABASE_NAME

_default_network_dir = Path("/mnt/netstorage/Data/pyNance/backend/app/data")
DATABASE_BASE_DIR = Path(os.getenv("DATABASE_BASE_DIR", _default_network_dir)).expanduser()
if not DATABASE_BASE_DIR.is_absolute():
    DATABASE_BASE_DIR = (DIRECTORIES["DATA_DIR"] / DATABASE_BASE_DIR).resolve(
        strict=False
    )
else:
    DATABASE_BASE_DIR = DATABASE_BASE_DIR.resolve(strict=False)

CURRENT_DATABASE_PATH = DATABASE_BASE_DIR / DATABASE_NAME

DATABASE_PATH = DATABASE_BACKUP_PATH
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
TELEMETRY = {"enabled": True, "track_modifications": False}

# Path to the R/S arbitrage dashboard data produced by the Discord bot.
# The TUI script should write JSON snapshots to this file for consumption
# by the web API.
ARBITRAGE_FILE = DIRECTORIES["LOGS_DIR"] / "rs_arbitrage.json"
