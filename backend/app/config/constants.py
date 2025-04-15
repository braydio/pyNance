
# backend/app/config/constants.py
from .paths import DIRECTORIES

FILES = {
    "LINKED_ACCOUNTS": DIRECTORIES["DATA_DIR"] / "LinkAccounts.json",
    "LINKED_ITEMS": DIRECTORIES["DATA_DIR"] / "LinkItems.json",
    "INVESTMENTS": DIRECTORIES["DATA_DIR"] / "LinkInvestments.json",
    "TRANSACTIONS": DIRECTORIES["DATA_DIR"] / "Transactions.json",
    "TRANSACTIONS_RAW": DIRECTORIES["TEMP_DIR"] / "RichTransactionsRaw.json",
    "TRANSACTIONS_EXPORT": DIRECTORIES["TEMP_DIR"] / "Transactions.json",
    "TRANSACTIONS_RAW_ENRICHED": DIRECTORIES["TEMP_DIR"] / "TransactionsRawEnriched.json",
    "DEFAULT_THEME": DIRECTORIES["THEMES_DIR"] / "default.css",
    "CURRENT_THEME": DIRECTORIES["THEMES_DIR"] / "current_theme.txt",
    "ARCHIVE_FILE": DIRECTORIES["ARCHIVE_DIR"] / "archive.json",
    "PLAID_TOKENS": DIRECTORIES["DATA_DIR"] / "PlaidTokens.json",
    "TELLER_TOKENS": DIRECTORIES["DATA_DIR"] / "TellerDotTokens.json",
    "TELLER_ACCOUNTS": DIRECTORIES["DATA_DIR"] / "TellerDotAccounts.json",
    "TELLER_DOT_CERT": DIRECTORIES["CERTS_DIR"] / "certificate.pem",
    "TELLER_DOT_KEY": DIRECTORIES["CERTS_DIR"] / "private_key.pem"
}

SQLALCHEMY_DATABASE_URI = f"sqlite:///{DIRECTORIES['DATA_DIR']}/pynance_dashroad.db"
TELEMETRY = {
    "enabled": True,
    "track_modifications": False
}

