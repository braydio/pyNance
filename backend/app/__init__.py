from app.config import logger
from app.extensions import db
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    CORS(app)

    # Load configuration from config.py
    app.config.from_object("app.config")

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Import blueprints from routes/teller.py and charts
    from app.routes.charts import charts
    from app.routes.plaid_investments import plaid_investments
    from app.routes.plaid_transactions import plaid_transactions
    from app.routes.teller_transactions import teller_transactions

    # Register blueprints with appropriate URL prefixes
    app.register_blueprint(charts, url_prefix="/api/charts")
    app.register_blueprint(teller_transactions, url_prefix="/api/teller/transactions")
    app.register_blueprint(plaid_transactions, url_prefix="/api/plaid/transactions")
    app.register_blueprint(plaid_investments, url_prefix="/api/plaid/investments")

    logger.debug(
        "Blueprints registered: charts under '/api/charts', teller endpoints under '/api/transactions/teller', plaid transactions under '/api/transactions/plaid' and plaid investments at '/api/investments/plaid'"
    )
    return app
