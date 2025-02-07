import json
import os
from datetime import datetime

from app.plaid_api import (
    exchange_public_token,
    get_item_info,
    refresh_plaid_item,
    save_initial_account_data,
)
from config import DIRECTORIES, FILES, setup_logger
from flask import Blueprint, jsonify, render_template, request

logger = setup_logger()
main = Blueprint("main", __name__)

LINKED_ITEMS = FILES["LINKED_ITEMS"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]
TRANSACTIONS_LIVE = FILES["TRANSACTIONS_LIVE"]
TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]


@main.route("/")
def dashboard():
    logger.debug("Rendering dashboard.html")
    return render_template("dashboard.html")


@main.route("/refresh_item", methods=["POST"])
def refresh_item():
    data = request.json
    item_id = data.get("item_id")
    product = data.get("product")
    if not item_id or not product:
        return jsonify({"error": "Missing item_id or product type"}), 400
    try:
        with open(LINKED_ITEMS, "r") as f:
            linked_items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Could not load linked items"}), 500
    item_data = linked_items.get(item_id)
    if not item_data:
        return jsonify({"error": f"Item ID {item_id} not found"}), 404
    access_token = item_data.get("access_token")
    if not access_token:
        return jsonify({"error": f"Access token not found for item {item_id}"}), 400
    if product not in item_data.get("products", []):
        return (
            jsonify({"error": f"Product {product} not linked to item {item_id}"}),
            400,
        )
    response_data = refresh_plaid_item(access_token, product)
    if not response_data:
        return (
            jsonify({"error": f"Failed to refresh {product} for item {item_id}"}),
            500,
        )
    item_status = item_data.get("status", {})
    item_status.setdefault("transactions", {})[
        "last_successful_update"
    ] = datetime.utcnow().isoformat()
    item_data["status"] = item_status
    linked_items[item_id] = item_data
    with open(LINKED_ITEMS, "w") as f:
        json.dump(linked_items, f, indent=4)
    return jsonify(
        {"status": "success", "message": f"{product} refreshed", "data": response_data}
    )


@main.route("/save_public_token", methods=["POST"])
def save_public_token():
    try:
        if not request.is_json:
            logger.error("Invalid request: Content-Type must be application/json")
            return (
                jsonify({"error": "Invalid Content-Type. Must be application/json."}),
                400,
            )
        data = request.get_json()
        logger.debug(f"Received POST data: {json.dumps(data, indent=2)}")
        public_token = data.get("public_token")
        if public_token:
            temp_dir = DIRECTORIES["TEMP_DIR"]
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            with open(os.path.join(temp_dir, "public_token.txt"), "w") as f:
                f.write(public_token)
            logger.info("Public token saved to file")
            access_token = exchange_public_token(public_token)
            if access_token:
                item_id, institution_name = get_item_info(access_token)
                if item_id:
                    save_initial_account_data(access_token, item_id)
                    logger.info(f"Linked to {institution_name} with item ID: {item_id}")
                    return (
                        jsonify(
                            {
                                "message": f"Linked to {institution_name} successfully",
                                "access_token": access_token,
                            }
                        ),
                        200,
                    )
                else:
                    logger.error("Failed to retrieve item metadata")
                    return jsonify({"error": "Failed to retrieve item metadata"}), 400
            else:
                logger.error("No public token provided")
                return jsonify({"error": "No public token provided"}), 400
    except Exception as e:
        logger.error(f"Error processing public token: {e}")
        return jsonify({"error": "Server error", "details": str(e)}), 500
