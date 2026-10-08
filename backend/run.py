"""Local development entrypoint for the Flask app."""

from pathlib import Path

from app import create_app
from flask_migrate import upgrade

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _upgrade_database(app) -> None:
    """Apply committed Alembic revisions before serving the local app."""

    with app.app_context():
        if app.config.get("ENV") == "production":
            raise RuntimeError("Refusing local startup migrations in production; deploy startup applies migrations.")
        upgrade(directory=str(MIGRATIONS_DIR))


def main() -> None:
    app = create_app()
    _upgrade_database(app)
    app.run(host="0.0.0.0", static_files="static", port=5000, debug=True)


if __name__ == "__main__":
    main()
