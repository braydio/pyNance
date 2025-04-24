import logging
import os
import sys
from pathlib import Path
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


def setup_logger():
    logger = logging.getLogger()
    if not logger.hasHandlers():
        log_path = DIRECTORIES["LOGS_DIR"] / "app.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Base file log (always at DEBUG level)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler based on LOG_LEVEL
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

        # If VERBOSE enabled, enable annoying level for console
        if VERBOSE_LOGGING:
            console_handler.setLevel(min(console_handler.level, VERBOSE_LEVEL_NUM))
        else:
            logging.disable(VERBOSE_LEVEL_NUM)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.setLevel(logging.DEBUG)  # Always allow lowest through pipeline
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.info(
            f"Logging initialized. LOG_LEVEL={LOG_LEVEL}, VERBOSE_LOGGING={VERBOSE_LOGGING}"
        )

    return logger
