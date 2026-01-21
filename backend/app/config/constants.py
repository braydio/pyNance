# backend/app/config/constants.py

"""Centralized file paths and runtime constants for the Flask backend."""

import os

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from .environment import DB_SCHEMA, IS_PROD
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
}

FRONTEND_DIST_DIR = os.path.join(os.path.dirname(__file__), "../../../frontend/dist")

SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"options": f"-c search_path={DB_SCHEMA}"}}
if not SQLALCHEMY_DATABASE_URI:
    raise RuntimeError(
        "SQLALCHEMY_DATABASE_URI must be defined when running against PostgreSQL."
    )

try:
    _parsed_uri = make_url(SQLALCHEMY_DATABASE_URI)
    DATABASE_NAME = _parsed_uri.database
    if IS_PROD and DB_SCHEMA != "public":
        raise RuntimeError(
            f"Production environment may only use DB_SCHEMA='public' "
            f"(got {DB_SCHEMA!r})"
        )
except ArgumentError as exc:  # pragma: no cover - misconfiguration guard
    raise RuntimeError(
        "SQLALCHEMY_DATABASE_URI is not a valid SQLAlchemy URL."
    ) from exc
DB_IDENTITY = f"{DATABASE_NAME}:{DB_SCHEMA}"

TELEMETRY = {"enabled": True, "track_modifications": False}

# Path to the R/S arbitrage dashboard data produced by the Discord bot.
# The TUI script should write JSON snapshots to this file for consumption
# by the web API.
ARBITRAGE_FILE = DIRECTORIES["LOGS_DIR"] / "rs_arbitrage.json"

# Primary log file written by the RSAssistant process. The Arbit dashboard
# exposes a lightweight endpoint to read recent entries for the live feed.
RS_ASSISTANT_LOG_FILE = DIRECTORIES["LOGS_DIR"] / "rsassistant.log"
