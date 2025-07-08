"""Logging configuration utilities and helpers used across the backend."""

import functools
import logging
import os
import sys

from .paths import DIRECTORIES

# --- Custom VERBOSE level
VERBOSE_LEVEL_NUM = 15
logging.addLevelName(VERBOSE_LEVEL_NUM, "VERBOSE")


def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_LEVEL_NUM):
        self._log(VERBOSE_LEVEL_NUM, message, args, **kwargs)


logging.Logger.verbose = verbose

# --- Environment-driven settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        VERBOSE_LEVEL_NUM: "\033[41m",  # Red background
        logging.CRITICAL: "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


def with_verbose_logging(logger_name="verbose"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            previous_level = logger.level
            logger.setLevel(VERBOSE_LEVEL_NUM)
            logger.verbose(f"[with_verbose_logging] Entering {func.__name__}()")
            try:
                return func(*args, **kwargs)
            finally:
                logger.verbose(f"[with_verbose_logging] Exiting {func.__name__}()")
                logger.setLevel(previous_level)

        return wrapper

    return decorator


def setup_logger():
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        log_path = DIRECTORIES["LOGS_DIR"] / "app.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Main file log (all levels)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler for regular logs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Verbose logger (separate namespace + console + file)
        if VERBOSE_LOGGING:
            verbose_logger = logging.getLogger("verbose")
            verbose_logger.setLevel(VERBOSE_LEVEL_NUM)

            # Magenta-colored console output
            verbose_console = logging.StreamHandler(sys.stdout)
            verbose_console.setLevel(VERBOSE_LEVEL_NUM)

            class VerboseOnlyFilter(logging.Filter):
                def filter(self, record):
                    return record.levelno == VERBOSE_LEVEL_NUM

            class VerboseColorFormatter(logging.Formatter):
                COLORS = {
                    VERBOSE_LEVEL_NUM: "\033[41m",  # Red i think
                }
                RESET = "\033[0m"

                def format(self, record):
                    color = self.COLORS.get(record.levelno, "")
                    message = super().format(record)
                    return f"{color}{message}{self.RESET}"

            verbose_console.addFilter(VerboseOnlyFilter())
            verbose_console.setFormatter(
                VerboseColorFormatter("[%(asctime)s] [%(levelname)s] %(message)s")
            )

            verbose_log_path = DIRECTORIES["LOGS_DIR"] / "verbose.log"
            verbose_file = logging.FileHandler(verbose_log_path, encoding="utf-8")
            verbose_file.setLevel(VERBOSE_LEVEL_NUM)
            verbose_file.setFormatter(
                VerboseColorFormatter("[%(asctime)s] [%(levelname)s] %(message)s")
            )

            verbose_logger.addHandler(verbose_console)
            verbose_logger.addHandler(verbose_file)

        root_logger.info(
            f"Logging initialized. LOG_LEVEL={LOG_LEVEL}, VERBOSE_LOGGING={VERBOSE_LOGGING}"
        )

    return logging.getLogger()
