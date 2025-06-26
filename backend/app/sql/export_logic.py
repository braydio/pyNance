# backend/app/sql/export_logic.py
"""CSV export helpers for streaming large tables.

This module provides helpers to export model data to CSV without loading all
rows into memory at once. Queries are streamed using ``yield_per`` to avoid
excessive memory usage.
"""

import csv
import io

from app.config import logger
from app.extensions import db
from app.models import Account, RecurringTransaction, Transaction
from flask import current_app, send_file

CHUNK_SIZE = 500


def generate_csv_bytes(model, chunk_size: int = CHUNK_SIZE) -> io.StringIO:
    """Return CSV contents for ``model`` streamed in chunks."""

    output = io.StringIO()
    writer = csv.writer(output)
    headers = [col.name for col in model.__table__.columns]
    writer.writerow(headers)

    query = db.session.query(model).yield_per(chunk_size)
    for row in query:
        writer.writerow([getattr(row, col) for col in headers])

    output.seek(0)
    return output


def export_csv_response(model_name):
    model_map = {
        "accounts": Account,
        "transactions": Transaction,
        "recurring_transactions": RecurringTransaction,
    }
    model = model_map.get(model_name)
    if not model:
        return None, f"Model '{model_name}' not found."

    csv_io = generate_csv_bytes(model)
    return send_file(
        io.BytesIO(csv_io.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{model_name}.csv",
    )


def export_all_to_csv(chunk_size: int = CHUNK_SIZE) -> None:
    """Export all configured models to CSV files in streaming fashion."""

    with current_app.app_context():
        tables = {
            "accounts.csv": Account,
            "transactions.csv": Transaction,
            "recurring_transactions.csv": RecurringTransaction,
        }

        for filename, model in tables.items():
            query = db.session.query(model).yield_per(chunk_size)

            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                headers = [col.name for col in model.__table__.columns]
                writer.writerow(headers)
                count = 0
                for row in query:
                    writer.writerow([getattr(row, col) for col in headers])
                    count += 1

            if count:
                logger.info(f"Exported {count} rows to {filename}")
            else:
                logger.info(f"No data for {model.__name__}")


def run_export() -> None:
    """Run :func:`export_all_to_csv` using an application context."""

    from app import create_app

    app = create_app()
    with app.app_context():
        export_all_to_csv()


if __name__ == "__main__":
    run_export()
