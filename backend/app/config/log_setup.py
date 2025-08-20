"""Logging configuration utilities and helpers used across the backend."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from .paths import DIRECTORIES

SQL_LOG_FILE = DIRECTORIES["LOGS_DIR"] / "sqlalchemy.log"
APP_LOG_FILE = DIRECTORIES["LOGS_DIR"] / "app.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

sql_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s %(filename)s:%(lineno)d - %(message)s"
)

# --- Clean SQLAlchemy logging with rotation ---
sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
sqlalchemy_logger.setLevel(logging.WARNING)

sql_file_handler = RotatingFileHandler(
    SQL_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
)
sql_file_handler.setFormatter(sql_formatter)
sqlalchemy_logger.addHandler(sql_file_handler)

# Optional: also show SQL in console for dev
if os.getenv("SQL_ECHO", "false").lower() == "true":
    sql_console_handler = logging.StreamHandler(sys.stdout)
    sql_console_handler.setFormatter(sql_formatter)
    sqlalchemy_logger.addHandler(sql_console_handler)

# --- App logging setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


def setup_logger():
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        APP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        # File log (INFO+ or as configured) with rotation
        file_handler = RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        # Respect configured LOG_LEVEL for file logging (default INFO)
        file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        color_fmt = ColorFormatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )

        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
            )
        )
        console_handler.setFormatter(color_fmt)

        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        root_logger.info(
            f"Logging initialized. LOG_LEVEL={LOG_LEVEL} (RotatingFileHandler, 10MB x5)"
        )

    return logging.getLogger()
