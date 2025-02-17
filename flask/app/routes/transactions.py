# app/routes/transactions.py
from app.config import FILES, logger
from app.helper_utils import load_transactions_json

from flask import Blueprint, jsonify, request

transactions_api = Blueprint(
    "transactions_api", __name__, url_prefix="/api/transactions"
)


@transactions_api.route("/", methods=["GET"])
def get_transactions():
    try:
        transactions = load_transactions_json(FILES["TRANSACTIONS_LIVE"]) or []
        page = request.args.get("page", "1")
        page_size = request.args.get("page_size", "50")
        if not page.isdigit() or not page_size.isdigit():
            return (
                jsonify(
                    {"status": "error", "message": "Invalid pagination parameters"}
                ),
                400,
            )
        page, page_size = int(page), int(page_size)
        paginated = transactions[(page - 1) * page_size : page * page_size]
        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"transactions": paginated, "total": len(transactions)},
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
