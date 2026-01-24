from sqlalchemy import text

from app.config import logger
from app.extensions import db


def ensure_transactions_sequence() -> None:
    bind = db.session.get_bind()
    if not bind or bind.dialect.name != "postgresql":
        return
    try:
        db.session.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('transactions','id'), "
                "(SELECT COALESCE(MAX(id), 0) FROM transactions))"
            )
        )
    except Exception as exc:
        logger.warning("Failed to sync transactions id sequence: %s", exc)
