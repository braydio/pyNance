# app/routes/accounts.py
import json

from config import FILES, logger

from flask import Blueprint, jsonify

accounts = Blueprint("accounts_api", __name__, url_prefix="/api/accounts")


@accounts.route("/", methods=["GET"])
def get_accounts():
    try:
        with open(FILES["LINKED_ACCOUNTS"], "r") as f:
            link_accounts = json.load(f)
        with open(FILES["LINKED_ITEMS"], "r") as f:
            link_items = json.load(f)

        accounts = []
        for account_id, account in link_accounts.items():
            item_data = link_items.get(account.get("item_id"), {})
            accounts.append(
                {
                    "id": account_id,
                    "name": account.get("account_name"),
                    "institution": account.get("institution_name"),
                    "type": account.get("type"),
                    "subtype": account.get("subtype"),
                    "balances": account.get("balances"),
                    "last_successful_update": item_data.get("status", {})
                    .get("transactions", {})
                    .get("last_successful_update"),
                    "products": item_data.get("products", []),
                }
            )
        return jsonify({"status": "success", "data": accounts}), 200
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/institutions", methods=["GET"])
def get_institutions():
    try:
        with open(FILES["LINKED_ITEMS"], "r") as f:
            link_items = json.load(f)
        with open(FILES["LINKED_ACCOUNTS"], "r") as f:
            link_accounts = json.load(f)

        institutions = {}
        for item_id, item_data in link_items.items():
            inst_name = item_data.get("institution_name", "Unknown Institution")
            last_update = (
                item_data.get("status", {})
                .get("transactions", {})
                .get("last_successful_update", "Never refreshed")
            )
            if inst_name not in institutions:
                institutions[inst_name] = {
                    "item_id": item_id,
                    "products": item_data.get("products", []),
                    "status": item_data.get("status", {}),
                    "accounts": [],
                    "last_successful_update": last_update,
                }
            for acc_id, acc_data in link_accounts.items():
                if acc_data.get("item_id") == item_id:
                    balance = acc_data.get("balances", {}).get("current", 0)
                    if acc_data.get("type") == "credit":
                        balance *= -1
                    institutions[inst_name]["accounts"].append(
                        {
                            "id": acc_id,
                            "name": acc_data.get("account_name", "Unknown Account"),
                            "type": acc_data.get("type", "Unknown"),
                            "subtype": acc_data.get("subtype", "Unknown"),
                            "balance": balance,
                        }
                    )
        return jsonify({"status": "success", "institutions": institutions}), 200
    except Exception as e:
        logger.error(f"Error fetching institutions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
