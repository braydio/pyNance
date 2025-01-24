import logging
import os
from dotenv import load_dotenv
from pathlib import Path

# Define directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"
THEMES_DIR = Path('Dash/static/themes')

# Make DIRs if not exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
THEMES_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('Dash/logs/testing.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Load environment variables
load_dotenv()
PLAID_CLIENT_ID = os.getenv("CLIENT_ID")
PLAID_SECRET = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PRODUCTS = os.getenv("PRODUCTS", "transactions").split(",")
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

# Define required json files (and css)
LINKED_ACCOUNTS = DATA_DIR / "LinkAccounts.json"
LINKED_ITEMS = DATA_DIR / "LinkItems.json"
LATEST_TRANSACTIONS = DATA_DIR / "Transactions.json"
LATEST_RESPONSE = TEMP_DIR / "ResponseTransactions.json"
TRANSACTION_REFRESH_FILE = TEMP_DIR /"TransactionRefresh.json"
DEFAULT_THEME = THEMES_DIR / "default.css"

logger.debug(f"Files loaded in /data: ")
logger.debug(f"{LINKED_ITEMS}")
logger.debug(f"{LINKED_ACCOUNTS}")
logger.debug(f"{LATEST_TRANSACTIONS}")

logger.debug(f"Temp files in /temp: ")
logger.debug(f"{LATEST_RESPONSE}")
logger.debug(f"{TRANSACTION_REFRESH_FILE}")

logger.debug(f"Static elements in /static: ")
logger.debug(f"{DEFAULT_THEME}")

logger.debug(f"Logging info to")
logger.debug(f"{LOGS_DIR}")

# Ensure directories exist - might be redundant
for dir_path in [THEMES_DIR, DATA_DIR, TEMP_DIR, LOGS_DIR]:
    if not dir_path.exists():
        logging.warning(f"Directory {dir_path} does not exist. Creating it...")
        dir_path.mkdir(parents=True, exist_ok=True)
