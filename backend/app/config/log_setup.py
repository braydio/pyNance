
"""Logging configuration utilities and helpers used across the backend.

The module respects the ``LOG_LEVEL`` environment variable (defaulting to
``INFO``) for the root logger and both console/file handlers. The console
handler uses ANSI color codes, while the file handler rotates at 10MB with
five backups.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .paths import DIRECTORIES

SQL_LOG_FILE = DIRECTORIES["LOGS_DIR"] / "sqlalchemy.log"
APP_LOG_FILE = DIRECTORIES["LOGS_DIR"] / "app.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

sql_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s %(filename)s:%(lineno)d - %(message)s"
)

# ---------------------------------------------------------------------------
#   SQLAlchemy Logging (Rotating, quiet by default)
# ---------------------------------------------------------------------------
sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
sqlalchemy_logger.setLevel(logging.WARNING)

sql_file_handler = RotatingFileHandler(
    SQL_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
)
sql_file_handler.setFormatter(sql_formatter)
sqlalchemy_logger.addHandler(sql_file_handler)

if os.getenv("SQL_ECHO", "false").lower() == "true":
    sql_console_handler = logging.StreamHandler(sys.stdout)
    sql_console_handler.setFormatter(sql_formatter)
    sqlalchemy_logger.addHandler(sql_console_handler)

# ---------------------------------------------------------------------------
#   App Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[94m",
        logging.INFO: "\033[92m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[91m",
        logging.CRITICAL: "\033[95m",
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        return f"{color}{super().format(record)}{self.RESET}"


def setup_logger():
    """
    Configure root logger with:
      - single rotating file handler
      - single colored console handler
      - honoring LOG_LEVEL
      - suppressing noisy libs (werkzeug, urllib3, botocore)
    """
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Helper predicates
    def is_app_file_handler(h):
        return (
            isinstance(h, RotatingFileHandler)
            and Path(getattr(h, "baseFilename", "")) == APP_LOG_FILE
        )

    def is_console_handler(h):
        return isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) in (
            sys.stdout,
            sys.stderr,
        )

    existing_file = any(is_app_file_handler(h) for h in root_logger.handlers)
    existing_console = any(is_console_handler(h) for h in root_logger.handlers)

    # Create log directory if needed
    if not existing_file or not existing_console:
        APP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ----------------------------
    # File Handler
    # ----------------------------
    if not existing_file:
        file_handler = RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
            )
        )
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    # ----------------------------
    # Console Handler
    # ----------------------------
    if not existing_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            ColorFormatter(
                "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
            )
        )
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

    # ----------------------------
    # Normalize handler levels
    # ----------------------------
    for handler in root_logger.handlers:
        if is_app_file_handler(handler) or is_console_handler(handler):
            handler.setLevel(log_level)

    # ----------------------------
    # Silence noisy libs once
    # ----------------------------
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.ERROR)

    # Only log once after full setup
    root_logger.info(
        "Logging initialized. LOG_LEVEL=%s (RotatingFileHandler, 10MB x%d)",
        LOG_LEVEL,
        BACKUP_COUNT,
    )

    return root_logger

