# File: app/__init__.py

from app.config import logger
from app.extensions import db
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate  # New import


def create_app():
    app = Flask(__name__)

    CORS(app)
    app.config.from_object("app.config")
    db.init_app(app)
    Migrate(app, db)  # Initialize Flask-Migrate

    with app.app_context():
        from app.helpers.plaid_helpers import refresh_plaid_categories
        refresh_plaid_categories()
        # Ensure models are imported so that tables are registered
        # db.create_all()
        # Import and register blueprints
        from app.routes.transactions import transactions
        from app.routes.accounts import accounts
        from app.routes.recurring import recurring
        from app.routes.charts import charts
        from app.routes.categories import categories as categories_bp
        from app.routes.export import export
        from app.routes.plaid import plaid_bp
        from app.routes.plaid_investments import plaid_investments
        from app.routes.plaid_transactions import plaid_transactions
        from app.routes.teller_transactions import teller_transactions

        app.register_blueprint(export, url_prefix="/api/export")
        app.register_blueprint(categories_bp, url_prefix="/api/categories")
        app.register_blueprint(transactions, url_prefix="/api/transactions")
        app.register_blueprint(accounts, url_prefix="/api/accounts")
        app.register_blueprint(charts, url_prefix="/api/charts")
        app.register_blueprint(recurring, url_prefix="/api/recurring")
        app.register_blueprint(plaid_bp, url_prefix="/api/plaid")
        app.register_blueprint(
            teller_transactions, url_prefix="/api/teller/transactions"
        )
        app.register_blueprint(plaid_transactions, url_prefix="/api/plaid/transactions")
        app.register_blueprint(plaid_investments, url_prefix="/api/plaid/investments")


    return app
