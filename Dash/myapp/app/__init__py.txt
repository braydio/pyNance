from app.debug import debug as debug_blueprint
from app.routes import main as main_blueprint
from app.settings import settings as settings_blueprint
from config import setup_logger
from flask import Flask
from sql_utils import init_db

logger = setup_logger()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Initialize the SQL database.
    init_db()

    # Register blueprints.
    app.register_blueprint(main_blueprint)
    app.register_blueprint(settings_blueprint)
    app.register_blueprint(debug_blueprint)

    return app
