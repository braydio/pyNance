"""CSV export routes for various models."""

import csv
from io import StringIO

from app.extensions import db
from app.models import Account, PlaidAccount, TellerAccount
from app.sql.export_logic import export_all_to_csv, export_csv_response
from flask import Blueprint, Response, jsonify

export = Blueprint("export", __name__)


@export.route("/<model_name>", methods=["GET"])
def export_model_csv(model_name):
    try:
        response = export_csv_response(model_name)
        if response is None:
            return (
                jsonify(
                    {"status": "error", "message": f"Unknown model '{model_name}'"}
                ),
                404,
            )
        return response
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@export.route("/all", methods=["GET"])
def export_all_models():
    try:
        export_all_to_csv()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "All models exported to local CSV files.",
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@export.route("/access_token_export", methods=["GET"])
def export_accounts_csv():
    """Export active account access tokens for Plaid and Teller."""
    plaid_tokens = (
        db.session.query(Account.user_id, PlaidAccount.access_token)
        .join(PlaidAccount, Account.account_id == PlaidAccount.account_id)
        .filter(Account.is_hidden.is_(False))
        .all()
    )
    teller_tokens = (
        db.session.query(Account.user_id, TellerAccount.access_token)
        .join(TellerAccount, Account.account_id == TellerAccount.account_id)
        .filter(Account.is_hidden.is_(False))
        .all()
    )

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["user_id", "access_token"])
    writer.writerows(plaid_tokens + teller_tokens)

    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=accounts_export.csv"},
    )
