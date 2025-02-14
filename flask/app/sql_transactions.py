# sq;_transactions.py
from config import logger
from sql_utils import SessionLocal, Transaction

from flask import Blueprint, jsonify, render_template, request

transact_route = Blueprint("transactions", __name__)


@transact_route.route("/transactions")
def transactions_page():
    return render_template("transactions.html")


@transact_route.route("/get_transactions", methods=["GET"])
def get_transactions():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    session = SessionLocal()
    try:
        query = session.query(Transaction).order_by(Transaction.date.desc())
        total = query.count()
        transactions = query.offset((page - 1) * page_size).limit(page_size).all()

        result = []
        for tx in transactions:
            result.append(
                {
                    "transaction_id": tx.transaction_id,
                    "date": tx.date.isoformat(),
                    "name": tx.name,
                    "amount": tx.amount,
                    "category": tx.category,
                    "merchant_name": tx.merchant_name,
                    # Optionally include account details if you set up relationships
                    "account_id": tx.account.id if tx.account else None,
                    "account_name": tx.account.account_name if tx.account else None,
                    "institution": tx.account.institution.name
                    if (tx.account and tx.account.institution)
                    else None,
                }
            )
        return (
            jsonify(
                {"status": "success", "data": {"transactions": result, "total": total}}
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()
