from config import DIRECTORIES, FILES, logger
from flask import Blueprint, jsonify, render_template, request

THEMES_DIR = DIRECTORIES["THEMES_DIR"]
CURRENT_THEME = FILES["CURRENT_THEME"]
DEFAULT_THEME = FILES["DEFAULT_THEME"]

settings = Blueprint("settings", __name__)


@settings.route("/settings")
def settings_page():
    return render_template("settings.html")


@settings.route("/themes", methods=["GET"])
def fetch_themes():
    """Fetch available themes and the current theme."""
    try:
        themes = get_available_themes()
        current_theme = get_current_theme()
        return jsonify({"themes": themes, "current_theme": current_theme}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings.route("/set_theme", methods=["POST"])
def change_theme():
    """Set a new theme."""
    data = request.json
    theme_name = data.get("theme")

    if not theme_name:
        return jsonify({"error": "No theme provided"}), 400

    try:
        if set_theme(theme_name):
            return jsonify({"success": True, "theme": theme_name}), 200
        else:
            return jsonify({"error": "Failed to set theme"}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@settings.context_processor
def inject_theme():
    return {"current_theme": get_current_theme()}


def get_available_themes():
    try:
        themes = [f.name for f in THEMES_DIR.glob("*.css")]
        logger.debug(f"Available themes: {themes}")
        return themes
    except Exception as e:
        logger.error(f"Error accessing themes directory: {e}")
        return []


def get_current_theme():
    """Get the currently active theme."""
    try:
        logger.info(f"Getting current theme {CURRENT_THEME}")
        if CURRENT_THEME.exists():
            with open(CURRENT_THEME, "r") as f:
                return f.read().strip()
        logger.info("No current theme file found. Using default theme.")
        return DEFAULT_THEME.name
    except Exception as e:
        logger.error(f"Error reading current theme: {e}")
        return DEFAULT_THEME.name


def set_theme(theme_name):
    """Set the active theme."""
    if theme_name not in get_available_themes():
        raise ValueError(f"Theme '{theme_name}' is not available.")
    try:
        with open(CURRENT_THEME, "w") as f:
            f.write(theme_name)
        logger.info(f"Theme updated to: {theme_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return False
