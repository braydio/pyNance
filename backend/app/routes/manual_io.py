import csv
import json
from io import TextIOWrapper
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Account
from app.helpers.plaid_helpers import get_item, get_accounts, get_institution_name
from app.sql import account_logic
from app.config import logger

manual_up = Blueprint("manual_up", __name__)


def safe_json(obj):
    """Convert Plaid model objects or unknown types into plain data"""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif isinstance(obj, list):
        return [safe_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    return str(obj)


@manual_up.route("/upload/accounts", methods=["POST"])
def upload_accounts_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    stream = TextIOWrapper(file.stream, encoding="utf-8")
    reader = csv.DictReader(stream)

    count = 0
    for row in reader:
        user_id = row.get("user_id")
        access_token = row.get("access_token")
        if not user_id:
            continue

        account = db.session.query(Account).filter_by(user_id=user_id).first()
        if account:
            account.access_token = access_token
        else:
            new = Account(
                user_id=user_id, access_token=access_token, account_id="TEMP-ID"
            )
            db.session.add(new)
        count += 1

    db.session.commit()
    return jsonify({"status": f"Upserted {count} records"})


@manual_up.route("/plaid_upload_token", methods=["POST"])
def manual_up_plaid():
    data = request.get_json()
    access_token = data.get("access_token")
    user_id = data.get("user_id")

    if not access_token or not user_id:
        return jsonify({"error": "Missing access_token or user_id"}), 400

    try:
        item_info = get_item(access_token)
        institution_id = item_info.get("institution_id", "Unknown")
        institution_name = get_institution_name(institution_id)

        accounts_data = get_accounts(access_token)

        # If accounts_data is a list, treat it as raw accounts
        accounts_list = (
            accounts_data
            if isinstance(accounts_data, list)
            else accounts_data.get("accounts", [])
        )

        logger.debug(json.dumps(safe_json(accounts_data), indent=2))
        with open("plaid_raw_response.json", "w") as f:
            json.dump(safe_json(accounts_data), f, indent=2)

        logger.info(
            f"[manual_up_plaid] Retrieved {len(accounts_list)} accounts for user {user_id}"
        )

        transformed = []
        for acct in accounts_list:
            transformed.append(
                {
                    "id": acct.get("account_id"),
                    "name": acct.get("name")
                    or acct.get("official_name", "Unnamed Account"),
                    "type": str(acct.get("type") or "Unknown"),
                    "subtype": str(acct.get("subtype") or "Unknown"),
                    "balance": {"current": acct.get("balances", {}).get("current", 0)},
                    "status": "active",
                    "institution": {"name": institution_name},
                    "access_token": access_token,
                    "enrollment_id": "",
                    "links": {},
                    "provider": "Plaid",
                }
            )

        account_logic.upsert_accounts(user_id, transformed, provider="Plaid")

        return jsonify(
            {
                "status": "success",
                "institution_name": institution_name,
                "account_count": len(transformed),
            }
        ), 200

    except Exception as e:
        logger.error(f"[manual_up_plaid] Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
