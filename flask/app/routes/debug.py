# app/routes/debug.py
from pathlib import Path

from app.config import DIRECTORIES

from flask import Blueprint, jsonify

debug_api = Blueprint("debug_api", __name__, url_prefix="/api/debug")


@debug_api.route("/info", methods=["GET"])
def debug_info():
    info = {
        "cwd": str(Path.cwd()),
        "templates": "templates",
        "static": "static",
        "themes": str(DIRECTORIES["THEMES_DIR"].resolve()),
        "data": str(DIRECTORIES["DATA_DIR"].resolve()),
        "temp": str(DIRECTORIES["TEMP_DIR"].resolve()),
    }
    return jsonify(info)
