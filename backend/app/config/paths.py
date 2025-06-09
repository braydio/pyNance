# backend/app/config/paths.py

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DIRECTORIES = {
    "DATA_DIR": BASE_DIR / "data",
    "IMPORT_DIR": BASE_DIR / "data" / "imports`",
    "CERTS_DIR": BASE_DIR / "certs",
    "TEMP_DIR": BASE_DIR / "temp",
    "LOGS_DIR": BASE_DIR / "logs",
    "ARCHIVE_DIR": BASE_DIR / "archive",
    "CONFIG_DIR": BASE_DIR / "config",
    "THEMES_DIR": BASE_DIR / "themes",
}

for path in DIRECTORIES.values():
    path.mkdir(parents=True, exist_ok=True)
