"""Application factory for the Flask backend."""

import sys

from app.cli.sync import sync_accounts
from app.config import logger, plaid_client
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
    from app.routes.dashboard import dashboard
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
    from app.routes.planning import planning
    from app.routes.recurring import recurring
    from app.routes.rules import rules as rules_bp
    from app.routes.summary import summary
    from app.routes.transactions import transactions

    app.register_blueprint(frontend, url_prefix="/")
    app.register_blueprint(export, url_prefix="/api/export")
    app.register_blueprint(dashboard, url_prefix="/api/dashboard")
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
    app.register_blueprint(planning, url_prefix="/api/planning")
    app.register_blueprint(institutions, url_prefix="/api/institutions")
    app.register_blueprint(summary, url_prefix="/api/summary")

    if ENABLE_ARBIT_DASHBOARD:
        from app.routes.arbit_dashboard import arbit_dashboard

        app.register_blueprint(arbit_dashboard, url_prefix="/api/arbit")

    app.cli.add_command(sync_accounts)
    # Dev CLI: seed demo data into a fresh database
    from app.cli.seed_dev import seed_dev

    app.cli.add_command(seed_dev)
    # Dev CLI: reconcile local Items with Plaid live status
    from app.cli.reconcile_plaid_items import reconcile_plaid_items

    app.cli.add_command(reconcile_plaid_items)

    # Utility CLI: import historic Account and PlaidAccount data from CSV
    from app.cli.import_accounts import import_accounts
    from app.cli.import_plaid_accounts import import_plaid_accounts

    app.cli.add_command(import_accounts)
    app.cli.add_command(import_plaid_accounts)

    # Utility CLI: import historic Plaid access tokens from CSV
    from app.cli.import_plaid_tokens import import_plaid_tokens

    app.cli.add_command(import_plaid_tokens)

    # Utility CLI: backfill Plaid transaction history over a custom range
    from app.cli.backfill_plaid_history import backfill_plaid_history
    from app.cli.debug_plaid_history import debug_plaid_history

    app.cli.add_command(backfill_plaid_history)
    app.cli.add_command(debug_plaid_history)

    # Dev CLI: run Plaid transactions/sync
    try:
        from app.cli.sync_plaid_transactions import sync_plaid_tx

        app.cli.add_command(sync_plaid_tx)
    except Exception:
        pass

    if plaid_client:
        logger.info("Plaid client initialized.")

    # Clean, grouped, colorized route logging
    with app.app_context():
        # 🎯 only GET routes (skip static, HEAD, OPTIONS)
        unique_routes = sorted(
            {
                rule.rule
                for rule in app.url_map.iter_rules()
                if "GET" in rule.methods
                and not rule.rule.startswith("/static")
                and not rule.rule.startswith("/favicon")
            }
        )

        # 📦 group by first path segment
        grouped = {}
        for route in unique_routes:
            parts = route.split("/")
            group = "/" + parts[1] if len(parts) > 1 else "/"
            grouped.setdefault(group, []).append(route)

        # 🎨 ANSI colors (console only)
        CYAN = "\033[96m"
        RESET = "\033[0m"

        lines = ["\n🔍 Registered Routes:"]
        for group in sorted(grouped):
            # color group header only in console
            colored_group = f"{CYAN}{group}{RESET}" if sys.stdout.isatty() else group
            lines.append(colored_group)

            for route in grouped[group]:
                if route != group:
                    lines.append(f"    {route}")

        logger.info("\n".join(lines))

    return app
