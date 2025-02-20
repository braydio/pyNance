import logging
import os
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
def setup_logger():
    logger = logging.getLogger(__name__)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        log_file = DIRECTORIES["LOGS_DIR"] / "testing.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger


logger = setup_logger()

# Load environment variables
load_dotenv()
PLAID_CLIENT_ID = os.getenv("CLIENT_ID")
PLAID_SECRET = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"
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
    "TELLER_TOKENS": DIRECTORIES["DATA_DIR"] / "TellerDotTokens.json",
    "TELLER_ACCOUNTS": DIRECTORIES["DATA_DIR"] / "TellerDotAccounts.json",
    "TELLER_DOT_CERT": DIRECTORIES["CERTS_DIR"] / "certificate.pem",
    "TELLER_DOT_KEY": DIRECTORIES["CERTS_DIR"] / "private_key.pem",
}

# Set the database URI (using SQLite here)
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DIRECTORIES['DATA_DIR'] / 'dashroad.db'}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

logger.debug("Directories initialized:")
for name, path in DIRECTORIES.items():
    logger.debug(f"{name}: {path}")
logger.debug("Files initialized:")
for name, path in FILES.items():
    logger.debug(f"{name}: {path}")

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
]
