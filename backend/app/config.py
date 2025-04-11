import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Define directories
BASE_DIR = Path(__file__).resolve().parent
DIRECTORIES = {
    "DATA_DIR": BASE_DIR / "data",
    "CERTS_DIR": BASE_DIR / "certs",
    "TEMP_DIR": BASE_DIR / "temp",
    "LOGS_DIR": BASE_DIR / "logs",
    "ARCHIVE_DIR": BASE_DIR / "archive",
    "CONFIG_DIR": BASE_DIR / "config",
    "THEMES_DIR": BASE_DIR / "themes",
}

# Ensure directories exist
for name, path in DIRECTORIES.items():
    path.mkdir(parents=True, exist_ok=True)


# Set up logging
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def setup_logger():
    logger = logging.getLogger(__name__)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        log_file = DIRECTORIES["LOGS_DIR"] / "testing.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger


logger = setup_logger()

# Load environment variables
load_dotenv()

# Dev Environment Variables - Use in test.py
VARIABLE_ENV_TOKEN = os.getenv("VARIABLE_ENV_TOKEN")
VARIABLE_ENV_ID = os.getenv("VARIABLE_ENV_ID")
print(f"{VARIABLE_ENV_TOKEN} {VARIABLE_ENV_ID}")

# Plaid API Env Variables
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET_KEY")
PLAID_CLIENT_NAME = os.getenv("PLAID_CLIENT_NAME")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

# Teller API Env Variables
TELLER_APP_ID = os.getenv("TELLER_APP_ID")
TELLER_API_BASE_URL = "https://api.teller.io"

# Define required files
FILES = {
    "LINKED_ACCOUNTS": DIRECTORIES["DATA_DIR"] / "LinkAccounts.json",
    "LINKED_ITEMS": DIRECTORIES["DATA_DIR"] / "LinkItems.json",
    "LINKED_INVESTMENT_ACCOUNTS": DIRECTORIES["DATA_DIR"] / "LinkInvestments.json",
    "TRANSACTIONS_LIVE": DIRECTORIES["DATA_DIR"] / "Transactions.json",
    "TRANSACTIONS_RAW_ENRICHED": DIRECTORIES["TEMP_DIR"] / "RichTransactionsRaw.json",
    "TRANSACTIONS_RAW": DIRECTORIES["TEMP_DIR"] / "RawTransactions.json",
    "DEFAULT_THEME": DIRECTORIES["THEMES_DIR"] / "default.css",
    "CURRENT_THEME": DIRECTORIES["THEMES_DIR"] / "current_theme.txt",
    "ARCHIVE_FILE": DIRECTORIES["ARCHIVE_DIR"] / "archive.json",
    "PLAID_TOKENS": DIRECTORIES["DATA_DIR"] / "PlaidTokens.json",
    "TELLER_TOKENS": DIRECTORIES["DATA_DIR"] / "TellerDotTokens.json",
    "TELLER_ACCOUNTS": DIRECTORIES["DATA_DIR"] / "TellerDotAccounts.json",
    "TELLER_DOT_CERT": DIRECTORIES["CERTS_DIR"] / "certificate.pem",
    "TELLER_DOT_KEY": DIRECTORIES["CERTS_DIR"] / "private_key.pem",
}

# Database URI using SQLite (SQLAlchemy)
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DIRECTORIES['DATA_DIR'] / 'pynance_dashroad.db'}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

logger.debug(f"SQL DB initialized: {SQLALCHEMY_DATABASE_URI}")

logger.debug("Directories initialized:")
# Don't need these all - look to cleanup and re-enable
# for name, path in DIRECTORIES.items():
#     logger.debug(f"{name}: {path}")
# logger.debug("Files initialized:")
# for name, path in FILES.items():
#     logger.debug(f"{name}: {path}")

logger.warning(f"Don't forget to remove these logs from config.py in {BASE_DIR}")
logger.debug(f"PLAID CLIENT ID {PLAID_CLIENT_ID}")
logger.debug(f"PLAID SECRET {PLAID_SECRET}")
logger.debug(f"PLAID API URL {PLAID_BASE_URL}")

# logger.debug(f"TELLER APP ID {TELLER_APP_ID}")
# logger.debug(f"TELLER API URL {TELLER_API_BASE_URL}")


DEBUG = True
# FLASK_ENV = "development"

__all__ = [
    "BASE_DIR",
    "DIRECTORIES",
    "FILES",
    "PLAID_CLIENT_ID",
    "PLAID_SECRET",
    "PLAID_ENV",
    "PRODUCTS",
    "PLAID_BASE_URL",
    "TELLER_APP_ID",
    "TELLER_API_BASE_URL",
    "VARIABLE_ENV_TOKEN",
    "VARIABLE_ENV_ID",
]
