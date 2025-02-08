from config import FILES
from flask import Blueprint, jsonify, render_template, request
from helper_utils import load_transactions_json

transactions = Blueprint("transactions", __name__)


@transactions.route("/transactions")
def transactions_page():
    return render_template("transactions.html")


@transactions.route("/get_transactions", methods=["GET"])
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

        page = int(page)
        page_size = int(page_size)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tx = transactions[start:end]

        formatted_transactions = [
            {
                "date": tx.get("date", "N/A"),
                "amount": tx.get("amount", 0.00),
                "name": tx.get("name", "N/A"),
                "category": tx.get("category", ["Uncategorized"]),
                "merchant_name": tx.get("merchant_name", "Unknown"),
                "account_name": tx.get("account_name", "Unknown Account"),
                "institution_name": tx.get("institution_name", "Unknown Institution"),
            }
            for tx in paginated_tx
        ]

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "transactions": formatted_transactions,
                        "total": len(transactions),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": str(e), "data": {"transactions": []}}
            ),
            500,
        )
