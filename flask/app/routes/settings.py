# app/routes/settings.py
from app.config import DIRECTORIES, FILES, logger

from flask import Blueprint, jsonify, request

settings_api = Blueprint("settings_api", __name__, url_prefix="/api/settings")


def get_available_themes():
    try:
        themes = [f.name for f in DIRECTORIES["THEMES_DIR"].glob("*.css")]
        return themes
    except Exception as e:
        logger.error(f"Error accessing themes: {e}")
        return []


def get_current_theme():
    try:
        if FILES["CURRENT_THEME"].exists():
            with open(FILES["CURRENT_THEME"], "r") as f:
                return f.read().strip()
        return FILES["DEFAULT_THEME"].name
    except Exception as e:
        logger.error(f"Error reading current theme: {e}")
        return FILES["DEFAULT_THEME"].name


@settings_api.route("/themes", methods=["GET"])
def fetch_themes():
    try:
        return (
            jsonify(
                {"themes": get_available_themes(), "current_theme": get_current_theme()}
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings_api.route("/set_theme", methods=["POST"])
def set_theme_route():
    data = request.get_json()
    theme_name = data.get("theme")
    if not theme_name:
        return jsonify({"error": "No theme provided"}), 400
    try:
        if theme_name not in get_available_themes():
            raise ValueError(f"Theme '{theme_name}' is not available.")
        with open(FILES["CURRENT_THEME"], "w") as f:
            f.write(theme_name)
        return jsonify({"success": True, "theme": theme_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
