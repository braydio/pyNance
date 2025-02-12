from pathlib import Path

from accounts import accounts
from charts import charts
from config import DIRECTORIES, FILES, setup_logger
from flask import Blueprint, Flask, jsonify, render_template, request
from plaid_endpoints import plaid_investments, plaid_transactions
from plaid_helpers import fetch_and_populate_categories
from settings import settings
from sql_utils import init_db
from transactions import transactions
from teller_dot_io import main_teller

logger = setup_logger()

debug = Blueprint("debug", __name__)


@debug.route("/testing")
def testing_view():
    """Render the testing.html template."""
    return render_template("testing.html")


@debug.route("/debug")
def debug_view():
    """Render the debug.html template."""
    return render_template("debug.html")


@debug.route("/debug/info")
def debug_info():
    return jsonify(
        {
            "current_working_directory": str(Path.cwd()),
            "template_folder": app.template_folder,
            "static_folder": app.static_folder,
            "themes_directory": str(THEMES_DIR.resolve()),
            "data_directory": str(DATA_DIR.resolve()),
            "temp_directory": str(TEMP_DIR.resolve()),
        }
    )


# Directories and file constants
DATA_DIR = DIRECTORIES["DATA_DIR"]
TEMP_DIR = DIRECTORIES["TEMP_DIR"]
LOGS_DIR = DIRECTORIES["LOGS_DIR"]
THEMES_DIR = DIRECTORIES["THEMES_DIR"]
LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
TRANSACTIONS_LIVE = FILES["TRANSACTIONS_LIVE"]
TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]
TRANSACTIONS_RAW_ENRICHED = FILES["TRANSACTIONS_RAW_ENRICHED"]
DEFAULT_THEME = FILES["DEFAULT_THEME"]
CURRENT_THEME = FILES["CURRENT_THEME"]

# === Configure Flask ===
app = Flask(__name__, template_folder="templates", static_folder="static")
app.register_blueprint(accounts)
app.register_blueprint(plaid_transactions)
app.register_blueprint(plaid_investments)
app.register_blueprint(settings)
app.register_blueprint(charts)
app.register_blueprint(debug)
app.register_blueprint(main_teller)


# === Main Flask App Routes ===
@app.route("/")
def dashboard():
    """Render the main dashboard."""
    logger.debug("Rendering dashboard.html")
    return render_template("dashboard.html")

@transactions.route("/transactions")
def transactions_page():
    return render_template("transactions.html")

@app.route("/teller-dot")
def teller_dot_homepage():
    return render_template("teller-dot.html")


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


@app.route("/themes", methods=["GET"])
def fetch_themes():
    """Fetch available themes and the current theme."""
    try:
        themes = get_available_themes()
        current_theme = get_current_theme()
        return jsonify({"themes": themes, "current_theme": current_theme}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_theme", methods=["POST"])
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


@app.context_processor
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


if __name__ == "__main__":
    logger.info("Starting Flask application, initializing SQL Database.")
    init_db()
    fetch_and_populate_categories()
    app.run(host="0.0.0.0", port=5000, debug=True)
