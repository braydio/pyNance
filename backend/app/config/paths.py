"""Define and create backend directory structure.

This module exposes common paths used by the backend. Each directory is created
on import so other modules can read and write files safely.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Directories used across the application. Paths are created automatically so
# helpers do not need to check for existence.
DIRECTORIES = {
    "DATA_DIR": BASE_DIR / "data",
    "IMPORT_DIR": BASE_DIR / "data" / "imports",
    "CERTS_DIR": BASE_DIR / "certs",
    "TEMP_DIR": BASE_DIR / "temp",
    "LOGS_DIR": BASE_DIR / "logs",
    "ARCHIVE_DIR": BASE_DIR / "archive",
    "CONFIG_DIR": BASE_DIR / "config",
    "THEMES_DIR": BASE_DIR / "themes",
}

for path in DIRECTORIES.values():
    path.mkdir(parents=True, exist_ok=True)
