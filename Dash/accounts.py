import json

from config import FILES, logger
from flask import Blueprint, jsonify, render_template, request

LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]

accounts = Blueprint("accounts", __name__)


@accounts.route("/accounts", methods=["GET"])
def accounts_page():
    try:
        with open(LINKED_ACCOUNTS) as f:
            link_accounts = json.load(f)
        with open(LINKED_ITEMS) as f:
            link_items = json.load(f)

        accounts_data = []
        for account_id, account in link_accounts.items():
            item_data = link_items.get(account.get("item_id"), {})
            accounts_data.append(
                {
                    "account_id": account_id,
                    "account_name": account.get("account_name"),
                    "institution_name": account.get("institution_name"),
                    "type": account.get("type"),
                    "subtype": account.get("subtype"),
                    "balances": account.get("balances"),
                    "last_successful_update": item_data.get("status", {})
                    .get("transactions", {})
                    .get("last_successful_update"),
                    "products": item_data.get("products", []),
                }
            )

        return render_template("accounts.html", accounts=accounts_data)
    except Exception as e:
        logger.error(f"Error loading accounts page: {e}")
        return render_template("error.html", error="Failed to load accounts data.")


@accounts.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        logger.info("Fetching account data...")
        try:
            with open(LINKED_ACCOUNTS) as f:
                accounts_data = json.load(f)
            logger.info(
                f"Loaded {len(accounts_data)} accounts from LinkedAccounts.json."
            )
        except FileNotFoundError:
            logger.error("LinkedAccounts.json file not found.")
            return (
                jsonify(
                    {"status": "error", "message": "LinkedAccounts.json not found"}
                ),
                404,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding LinkedAccounts.json: {e}")
            return (
                jsonify(
                    {"status": "error", "message": "Error decoding LinkedAccounts.json"}
                ),
                500,
            )

        accounts = [
            {
                "id": account_id,
                "name": account_data.get("account_name", "Unknown Account"),
                "institution": account_data.get(
                    "institution_name", "Unknown Institution"
                ),
                "masked_access_token": f"****{account_id[-4:]}",
                "balances": {
                    "available": account_data.get("balances", {}).get("available"),
                    "current": account_data.get("balances", {}).get("current"),
                },
            }
            for account_id, account_data in accounts_data.items()
        ]
        logger.info(f"Processed {len(accounts)} accounts.")
        return jsonify(accounts), 200

    except Exception as e:
        logger.error(f"Error loading accounts: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/get_institutions", methods=["GET"])
def get_institutions():
    try:
        logger.info("Fetching institutions and accounts data...")
        try:
            with open(LINKED_ITEMS) as f:
                link_items = json.load(f)
            logger.info(f"Loaded {len(link_items)} items from LinkedItems.json.")
        except FileNotFoundError:
            logger.error("LinkedItems.json file not found.")
            return (
                jsonify({"status": "error", "message": "LinkedItems.json not found"}),
                404,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding LinkedItems.json: {e}")
            return (
                jsonify(
                    {"status": "error", "message": "Error decoding LinkedItems.json"}
                ),
                500,
            )

        try:
            with open(LINKED_ACCOUNTS) as f:
                link_accounts = json.load(f)
            logger.info(
                f"Loaded {len(link_accounts)} accounts from LinkedAccounts.json."
            )
        except FileNotFoundError:
            logger.error("LinkedAccounts.json file not found.")
            return (
                jsonify(
                    {"status": "error", "message": "LinkedAccounts.json not found"}
                ),
                404,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding LinkedAccounts.json: {e}")
            return (
                jsonify(
                    {"status": "error", "message": "Error decoding LinkedAccounts.json"}
                ),
                500,
            )

        logger.info("Aggregating data by institution...")
        institutions = {}

        for item_id, item_data in link_items.items():
            institution_name = item_data.get("institution_name", "Unknown Institution")
            last_successful_update = (
                item_data.get("status", {})
                .get("transactions", {})
                .get("last_successful_update")
                or "Never refreshed"
            )

            if institution_name not in institutions:
                institutions[institution_name] = {
                    "item_id": item_id,
                    "products": item_data.get("products", []),
                    "status": item_data.get("status", {}),
                    "accounts": [],
                    "last_successful_update": last_successful_update,
                }
                logger.debug(
                    f"Added institution: {institution_name} with last refresh: {last_successful_update}"
                )

            linked_accounts_list = []
            for account_id, account_data in link_accounts.items():
                if account_data.get("item_id") == item_id:
                    balance = account_data.get("balances", {}).get("current", 0)
                    if account_data.get("type") == "credit":
                        balance *= -1
                    linked_accounts_list.append(
                        {
                            "account_id": account_id,
                            "account_name": account_data.get(
                                "account_name", "Unknown Account"
                            ),
                            "type": account_data.get("type", "Unknown"),
                            "subtype": account_data.get("subtype", "Unknown"),
                            "balances": {"current": balance},
                        }
                    )
            institutions[institution_name]["accounts"].extend(linked_accounts_list)
            logger.debug(
                f"{len(linked_accounts_list)} accounts linked to {institution_name}"
            )

        logger.info("Returning aggregated institution data.")
        return jsonify({"status": "success", "institutions": institutions}), 200

    except Exception as e:
        logger.error(f"Error fetching institutions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/save_group", methods=["POST"])
def save_group():
    try:
        data = request.json
        group_name = data.get("groupName")
        account_ids = data.get("accountIds")

        if not group_name or not account_ids:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Group name and accounts are required.",
                    }
                ),
                400,
            )

        group_data = {"name": group_name, "accounts": account_ids}
        with open("groups.json", "a") as f:
            f.write(json.dumps(group_data) + "\n")

        return (
            jsonify({"status": "success", "message": "Group saved successfully!"}),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
