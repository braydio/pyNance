# File: app/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from app.config import logger, plaid_client
from app.extensions import db
from app.config.environment import TELLER_WEBHOOK_SECRET


def create_app():
    app = Flask(__name__)

    # Core setup
    CORS(app)
    app.config.from_object("app.config")
    db.init_app(app)
    Migrate(app, db)

    # Import & execute setup tasks
    with app.app_context():
        from app.routes.categories import refresh_plaid_categories

        refresh_plaid_categories()

        # Import blueprints
        from app.routes.transactions import transactions
        from app.routes.accounts import accounts
        from app.routes.recurring import recurring
        from app.routes.manual_io import manual_up
        from app.routes.charts import charts
        from app.routes.categories import categories as categories_bp
        from app.routes.export import export
        from app.routes.plaid import plaid_bp
        from app.routes.plaid_investments import plaid_investments
        from app.routes.plaid_transactions import plaid_transactions
        from app.routes.teller_transactions import teller_transactions
        from app.routes.teller_webhook import webhooks, disabled_webhooks

        # Register blueprints with prefixes
        app.register_blueprint(export, url_prefix="/api/export")
        app.register_blueprint(categories_bp, url_prefix="/api/categories")
        app.register_blueprint(transactions, url_prefix="/api/transactions")
        app.register_blueprint(accounts, url_prefix="/api/accounts")
        app.register_blueprint(manual_up, url_prefix="/api/import")
        app.register_blueprint(charts, url_prefix="/api/charts")
        app.register_blueprint(recurring, url_prefix="/api/recurring")
        app.register_blueprint(plaid_bp, url_prefix="/api/plaid")
        app.register_blueprint(plaid_transactions, url_prefix="/api/plaid/transactions")
        app.register_blueprint(plaid_investments, url_prefix="/api/plaid/investments")
        app.register_blueprint(
            teller_transactions, url_prefix="/api/teller/transactions"
        )

        # Conditionally enable Teller webhook
        if TELLER_WEBHOOK_SECRET:
            app.register_blueprint(webhooks, url_prefix="/api/webhooks")
        else:
            app.register_blueprint(disabled_webhooks, url_prefix="/api/webhooks")

    return app
