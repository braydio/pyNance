import logging
import json
import os

THEMES_DIR = 'static/themes'

# Setup logging
logger = logging.getLogger(__name__)

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('Plaid/logs/plaid_api.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# Directory Functions
def ensure_directory_exists(directory_path):
    """Ensures a directory exists."""
    os.makedirs(directory_path, exist_ok=True)

# json Functions


