from flask import Blueprint, jsonify, render_template, request
from helper_utils import get_available_themes, get_current_theme, set_theme

settings = Blueprint("settings", __name__)


@settings.route("/settings")
def settings_page():
    return render_template("settings.html")


@settings.route("/themes", methods=["GET"])
def fetch_themes():
    try:
        themes = get_available_themes()
        current_theme = get_current_theme()
        return jsonify({"themes": themes, "current_theme": current_theme}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings.route("/set_theme", methods=["POST"])
def change_theme():
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
