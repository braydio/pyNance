"""Logging configuration utilities and helpers used across the backend.

The module respects the ``LOG_LEVEL`` environment variable (defaulting to
``INFO``) for the root logger and both console/file handlers. The console
handler uses ANSI color codes for readability, while the file handler rotates
at 10MB with five backups to preserve recent history without unbounded growth.
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
    """Colorize log levels for console readability."""
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
    """Configure the root logger and ensure handlers honor ``LOG_LEVEL``.

    The function applies the configured log level to the root logger and keeps
    the rotating file handler plus the colored console handler in sync with
    that level. Handlers are created if missing and reuse existing instances to
    avoid duplication.
    """
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    def is_app_file_handler(handler: logging.Handler) -> bool:
        return (
            isinstance(handler, RotatingFileHandler)
            and Path(getattr(handler, "baseFilename", "")) == APP_LOG_FILE
        )

    def is_console_handler(handler: logging.Handler) -> bool:
        return isinstance(handler, logging.StreamHandler) and getattr(
            handler, "stream", None
        ) in (sys.stdout, sys.stderr)

    file_handler_exists = any(
        is_app_file_handler(handler) for handler in root_logger.handlers
    )
    console_handler_exists = any(
        is_console_handler(handler)
        for handler in root_logger.handlers
        if not isinstance(handler, logging.PlaceHolder)
    )

    handlers_added = False
    if not file_handler_exists or not console_handler_exists:
        APP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not file_handler_exists:
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
        root_logger.addHandler(file_handler)
        handlers_added = True

    if not console_handler_exists:
        console_handler = logging.StreamHandler(sys.stdout)
        color_fmt = ColorFormatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        console_handler.setFormatter(color_fmt)
        root_logger.addHandler(console_handler)
        handlers_added = True

    for handler in root_logger.handlers:
        if is_app_file_handler(handler) or is_console_handler(handler):
            handler.setLevel(log_level)

    if handlers_added:
        root_logger.info(
            "Logging initialized. LOG_LEVEL=%s (RotatingFileHandler, 10MB x%d)",
            LOG_LEVEL,
            BACKUP_COUNT,
        )

    return root_logger
