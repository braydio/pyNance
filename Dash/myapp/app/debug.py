from pathlib import Path

from config import DATA_DIR, TEMP_DIR, THEMES_DIR
from flask import Blueprint, jsonify

debug = Blueprint("debug", __name__)


@debug.route("/debug")
def debug_info():
    return jsonify(
        {
            "current_working_directory": str(Path.cwd()),
            "themes_directory": str(THEMES_DIR.resolve()),
            "data_directory": str(DATA_DIR.resolve()),
            "temp_directory": str(TEMP_DIR.resolve()),
        }
    )
