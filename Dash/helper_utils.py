import json
import os
from pathlib import Path

from config import DIRECTORIES, logger

THEMES_DIR = DIRECTORIES["THEMES_DIR"]


def get_available_themes():
    try:
        themes = [f.name for f in THEMES_DIR.glob("*.css")]
        logger.debug(f"Available themes: {themes}")
        return themes
    except Exception as e:
        logger.error(f"Error accessing themes directory: {e}")
        return []


def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            resolved_path = Path(file_path).resolve()
            logger.debug(f"Loaded from {resolved_path}")
            return json.load(f)
    return {}


def save_json_with_backup(file_path, data):
    try:
        backup_path = f"{file_path}.bak"
        if os.path.exists(file_path):
            if os.path.exists(backup_path):
                logger.info(f"Overwriting stale backup: {backup_path}")
                os.remove(backup_path)
            os.rename(file_path, backup_path)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(
            f"Data successfully saved to {file_path}. Backup created at {backup_path}."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise e


def ensure_directory_exists(directory_path):
    os.makedirs(directory_path, exist_ok=True)


def ensure_file_exists(file_path, default_content=None):
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            if default_content is not None:
                if isinstance(default_content, (dict, list)):
                    json.dump(default_content, file, indent=2)
                else:
                    file.write(default_content)
            else:
                file.write("")
