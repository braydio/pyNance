# backend/app/sql/export_logic.py
import csv
import io
from flask import current_app, send_file
from app.extensions import db
from app.models import Account, Transaction, RecurringTransaction


def generate_csv_bytes(model):
    output = io.StringIO()
    writer = csv.writer(output)
    headers = [col.name for col in model.__table__.columns]
    writer.writerow(headers)

    rows = model.query.all()
    for row in rows:
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


def run_export():
    from app import create_app

    app = create_app()
    with app.app_context():
        export_all_to_csv()


if __name__ == "__main__":
    run_export()
