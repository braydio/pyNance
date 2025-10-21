"""Routes for uploading and processing manual financial data."""

import json
import os

from app.config import CLIENT_NAME, DIRECTORIES, logger
from app.extensions import db
from app.helpers.import_helpers import dispatch_import
from app.helpers.plaid_helpers import get_accounts as get_plaid_accounts
from app.helpers.plaid_helpers import get_institution_name, get_item
from app.models import Account
from app.sql import account_logic
from app.sql.manual_import_logic import upsert_imported_transactions
from flask import Blueprint, jsonify, request

IMPORT_DIR = DIRECTORIES["IMPORT_DIR"]
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
def auto_detect_and_upload():
    data = request.get_json()
    access_token = data.get("access_token")
    user_id = data.get("user_id")

    if not access_token or not user_id:
        return jsonify({"error": "Missing access_token or user_id"}), 400

    provider = "plaid"
    institution_name = "Unknown"

    try:
        item_info = get_item(access_token)
        inst_id = item_info.get("institution_id")
        institution_name = get_institution_name(inst_id)
        accounts_data = get_plaid_accounts(access_token)

        accounts = (
            accounts_data
            if isinstance(accounts_data, list)
            else accounts_data.get("accounts", [])
        )
        if not accounts:
            return jsonify({"error": "No accounts found with given token"}), 404

        formatted = []
        for acc in accounts:
            formatted.append(
                {
                    "id": acc.get("account_id") or acc.get("id"),
                    "name": acc.get("name")
                    or acc.get("official_name", "Unnamed Account"),
                    "type": str(acc.get("type") or "Unknown"),
                    "subtype": str(acc.get("subtype") or "Unknown"),
                    "balance": {"current": acc.get("balances", {}).get("current", 0)},
                    "status": acc.get("status", "active"),
                    "institution": {"name": institution_name},
                    "access_token": access_token,
                    "provider": provider,
                }
            )

        account_logic.upsert_accounts(user_id, formatted, provider=provider)
        logger.info(
            f"[manual_up] Uploaded {len(formatted)} accounts for {user_id} using {provider}"
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "provider": provider,
                    "account_count": len(formatted),
                    "institution_name": institution_name,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"[manual_up] Upload error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


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

        accounts_data = get_plaid_accounts(access_token)

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
                    "provider": "plaid",
                }
            )

        account_logic.upsert_accounts(user_id, transformed, provider="plaid")
        logger.info(
            f"[manual_up] Uploaded {len(transformed)} accounts for {user_id} using Plaid"
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "institution_name": institution_name,
                    "account_count": len(transformed),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"[manual_up_plaid] Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@manual_up.route("/import", methods=["POST"])
def import_selected_file():
    data = request.get_json()
    filename = data.get("file")
    if not filename:
        return jsonify({"error": "Missing file name."}), 400

    filepath = os.path.join(IMPORT_DIR, filename)
    logger.info(f"[IMPORT] Attempting to load file from: {filepath}")

    if not os.path.exists(filepath):
        return jsonify({"error": "File does not exist."}), 404

    try:
        result = dispatch_import(filepath)

        if result.get("status") == "success" and "data" in result:
            txns = result["data"]
            account_hint = (
                filename.split("_")[1] if "_" in filename else "Imported Account"
            )
            account = Account.query.filter_by(name=account_hint).first()
            if not account:
                account = Account(name=account_hint, type="credit", provider="manual")
                db.session.add(account)
                db.session.commit()

            inserted = upsert_imported_transactions(
                txns, user_id=CLIENT_NAME, account_id=account.account_id
            )
            result["inserted"] = inserted
            result["account"] = account.name

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@manual_up.route("/files", methods=["GET"])
def list_import_files():
    try:
        logger.info(f"[IMPORT FILES] Scanning: {IMPORT_DIR}")
        files = [
            f
            for f in os.listdir(IMPORT_DIR)
            if f.endswith((".csv", ".pdf"))
            and os.path.isfile(os.path.join(IMPORT_DIR, f))
        ]
        logger.info(f"[IMPORT FILES] Found: {files}")
        return jsonify(sorted(files))
    except Exception as e:
        logger.error(f"[IMPORT FILES ERROR] {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
