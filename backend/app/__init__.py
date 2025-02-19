from app.config import logger
from app.extensions import db

from flask import Flask


def create_app():
    app = Flask(__name__)

    # Load configuration from config.py
    app.config.from_object("app.config")

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Import models so that they are registered before creating tables

    with app.app_context():
        db.create_all()

    # Import blueprints from routes/teller.py
    from app.routes.charts import charts
    from app.routes.teller import link_teller, main_teller, transactions_bp

    # Register blueprints
    app.register_blueprint(link_teller, url_prefix="/api/teller")
    app.register_blueprint(main_teller, url_prefix="/api/teller")
    app.register_blueprint(charts, url_prefix="/api/charts")
    app.register_blueprint(transactions_bp, url_prefix="/api")

    logger.debug(
        "Blueprints registered: link_teller and main_teller under '/api/teller', transactions_bp under '/api'"
    )
    return app
