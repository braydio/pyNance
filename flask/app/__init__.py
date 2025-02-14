# app/__init__.py
from app.routes.accounts import accounts
from app.routes.charts import charts
from app.routes.debug import debug_api
from app.routes.plaid import plaid_api
from app.routes.settings import settings_api
from app.routes.teller import teller_api, teller_refresh_api
from app.routes.transactions import transactions_api
from config import setup_logger

from flask import Flask


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    setup_logger()

    # Register API blueprints with prefixes.
    app.register_blueprint(accounts)
    app.register_blueprint(charts, url_prefix="/api/charts")
    app.register_blueprint(plaid_api)
    app.register_blueprint(teller_api)
    app.register_blueprint(teller_refresh_api)
    app.register_blueprint(transactions_api)
    app.register_blueprint(settings_api)
    app.register_blueprint(debug_api)

    # Optionally: add a catch-all route to serve the Vue SPA
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return app.send_static_file("index.html")

    return app
