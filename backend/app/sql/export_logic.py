# backend/app/sql/export_logic.py
import csv
from flask import current_app
from app.extensions import db
from app.models import Account, Transaction, RecurringTransaction


def export_all_to_csv():
    with current_app.app_context():
        tables = {
            "accounts.csv": Account,
            "transactions.csv": Transaction,
            "recurring_transactions.csv": RecurringTransaction,
        }

        for filename, model in tables.items():
            rows = model.query.all()
            if not rows:
                print(f"No data for {model.__name__}")
                continue

            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                headers = [col.name for col in model.__table__.columns]
                writer.writerow(headers)
                for row in rows:
                    writer.writerow([getattr(row, col) for col in headers])

            print(f"Exported {len(rows)} rows to {filename}")


# Optional CLI trigger
def run_export():
    from app import create_app
    app = create_app()
    with app.app_context():
        export_all_to_csv()


if __name__ == "__main__":
    run_export()
