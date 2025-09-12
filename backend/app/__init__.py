"""Application factory for the Flask backend."""

from app.cli.sync import sync_accounts
from app.config import logger, plaid_client
from app.config.environment import TELLER_WEBHOOK_SECRET
from app.extensions import db
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate


def create_app():
    """Configure and return the Flask application instance."""
    from app.config import ARBIT_EXPORTER_URL, ENABLE_ARBIT_DASHBOARD

    app = Flask(__name__)
    CORS(app)
    app.config.from_object("app.config")
    app.config["ENABLE_ARBIT_DASHBOARD"] = ENABLE_ARBIT_DASHBOARD
    app.config["ARBIT_EXPORTER_URL"] = ARBIT_EXPORTER_URL
    db.init_app(app)
    Migrate(app, db)
    # Always register routes (for all environments)
    from app.routes.accounts import accounts
    from app.routes.arbitrage import arbitrage
    from app.routes.categories import categories
    from app.routes.charts import charts
    from app.routes.export import export
    from app.routes.forecast import forecast
    from app.routes.frontend import frontend
    from app.routes.goals import goals
    from app.routes.institutions import institutions
    from app.routes.investments import investments
    from app.routes.manual_io import manual_up
    from app.routes.plaid import plaid_routes
    from app.routes.plaid_investments import plaid_investments
    from app.routes.plaid_transactions import plaid_transactions
    from app.routes.plaid_webhook import plaid_webhooks
    from app.routes.plaid_webhook_admin import plaid_webhook_admin
    from app.routes.recurring import recurring
    from app.routes.rules import rules as rules_bp
    from app.routes.summary import summary
    from app.routes.teller import link_teller
    from app.routes.teller_transactions import teller_transactions
    from app.routes.teller_webhook import disabled_webhooks, webhooks
    from app.routes.transactions import transactions

    app.register_blueprint(frontend, url_prefix="/")
    app.register_blueprint(export, url_prefix="/api/export")
    app.register_blueprint(categories, url_prefix="/api/categories")
    app.register_blueprint(transactions, url_prefix="/api/transactions")
    app.register_blueprint(rules_bp, url_prefix="/api/rules")
    app.register_blueprint(accounts, url_prefix="/api/accounts")
    app.register_blueprint(manual_up, url_prefix="/api/import")
    app.register_blueprint(arbitrage, url_prefix="/api/arbitrage")
    app.register_blueprint(charts, url_prefix="/api/charts")
    app.register_blueprint(forecast, url_prefix="/api/forecast")
    app.register_blueprint(recurring, url_prefix="/api/recurring")
    app.register_blueprint(goals, url_prefix="/api/goals")
    app.register_blueprint(plaid_routes, url_prefix="/api/plaid")
    app.register_blueprint(plaid_transactions, url_prefix="/api/plaid/transactions")
    app.register_blueprint(plaid_webhooks, url_prefix="/api/webhooks")
    app.register_blueprint(plaid_webhook_admin, url_prefix="/api/plaid/webhook")
    app.register_blueprint(plaid_investments, url_prefix="/api/plaid/investments")
    app.register_blueprint(investments, url_prefix="/api/investments")
    app.register_blueprint(link_teller, url_prefix="/api/teller")
    app.register_blueprint(teller_transactions, url_prefix="/api/teller/transactions")
    app.register_blueprint(institutions, url_prefix="/api/institutions")
    app.register_blueprint(summary, url_prefix="/api/summary")

    if ENABLE_ARBIT_DASHBOARD:
        from app.routes.arbit_dashboard import arbit_dashboard

        app.register_blueprint(arbit_dashboard, url_prefix="/api/arbit")

    if TELLER_WEBHOOK_SECRET:
        app.register_blueprint(webhooks, url_prefix="/api/webhooks")
    else:
        app.register_blueprint(disabled_webhooks, url_prefix="/api/webhooks")
    app.cli.add_command(sync_accounts)
    # Dev CLI: reconcile local Items with Plaid live status
    from app.cli.reconcile_plaid_items import reconcile_plaid_items

    app.cli.add_command(reconcile_plaid_items)

    # Dev CLI: run Plaid transactions/sync
    try:
        from app.cli.sync_plaid_transactions import sync_plaid_tx

        app.cli.add_command(sync_plaid_tx)
    except Exception:
        pass

    if plaid_client:
        logger.info("Plaid client initialized.")

    # Optional: always log routes
    with app.app_context():
        routes = " \n ".join(str(rule) for rule in app.url_map.iter_rules())
        logger.info("🔍 Registered Routes:\n%s", routes)

    return app
