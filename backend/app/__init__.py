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
        # Ensure models are imported so that tables are registered

        db.create_all()

    # Import and register blueprints
    from app.routes.accounts import accounts
    from app.routes.charts import charts
    from app.routes.plaid_investments import plaid_investments
    from app.routes.plaid_transactions import plaid_transactions
    from app.routes.plaid import plaid_bp
    from app.routes.teller_transactions import teller_transactions

    app.register_blueprint(accounts, url_prefi="/api/accounts")
    app.register_blueprint(charts, url_prefix="/api/charts")
    app.register_blueprint(plaid_bp, url_prefix="/api/plaid")
    app.register_blueprint(teller_transactions, url_prefix="/api/teller/transactions")
    app.register_blueprint(plaid_transactions, url_prefix="/api/plaid/transactions")
    app.register_blueprint(plaid_investments, url_prefix="/api/plaid/investments")

    logger.debug(
        "Blueprints registered: charts (/api/charts), Teller (/api/teller/transactions), Plaid transactions (/api/plaid/transactions), and Plaid investments (/api/plaid/investments)"
    )
    return app
