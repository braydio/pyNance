# File: app/routes/charts.py
import random
from datetime import datetime, timedelta
import traceback

from app.config import logger
from app.extensions import db
from app.models import Account, Category, Transaction
from app.utils.finance_utils import normalize_account_balance
from flask import Blueprint, jsonify, request
from sqlalchemy import case, func

charts = Blueprint("charts", __name__)


@charts.route("/category_breakdown", methods=["GET"])
def category_breakdown():
    print(
        "Received query params:",
        request.args.get("start_date"),
        request.args.get("end_date"),
    )
    try:
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else datetime.now().date() - timedelta(days=30)
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_date_str
            else datetime.now().date()
        )

        transactions = (
            db.session.query(Transaction, Category)
            .join(Category, Transaction.category_id == Category.id)
            .join(Account, Transaction.account_id == Account.id)
            .filter(Transaction.amount < 0)
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .all()
        )

        breakdown_map = {}
        for tx, category in transactions:
            key = category.display_name or "Uncategorized"
            amt = normalize_account_balance(abs(tx.amount), tx.account.subtype)
            breakdown_map.setdefault(key, {"amount": 0, "date": tx.date})
            breakdown_map[key]["amount"] += amt
            if tx.date < breakdown_map[key]["date"]:
                breakdown_map[key]["date"] = tx.date

        data = [
            {
                "category": k,
                "amount": round(v["amount"], 2),
                "date": v["date"],
            }
            for k, v in breakdown_map.items()
        ]

        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/cash_flow", methods=["GET"])
def get_cash_flow():
    try:
        granularity = request.args.get("granularity", "monthly")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else None
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        )

        transactions = db.session.query(Transaction).join(
            Account, Transaction.account_id == Account.id
        )
        if start_date:
            transactions = transactions.filter(Transaction.date >= start_date)
        if end_date:
            transactions = transactions.filter(Transaction.date <= end_date)

        all_tx = transactions.all()

        groups = {}
        for tx in all_tx:
            key = (
                tx.date.strftime("%Y-%m-%d")
                if granularity == "daily"
                else tx.date.strftime("%m-%Y")
            )
            amt = normalize_account_balance(tx.amount, tx.account.subtype)
            if key not in groups:
                groups[key] = {"income": 0, "expenses": 0}
            if amt > 0:
                groups[key]["income"] += amt
            else:
                groups[key]["expenses"] += abs(amt)

        data = [
            {"date": k, "income": v["income"], "expenses": v["expenses"]}
            for k, v in sorted(groups.items())
        ]

        total_income = sum(item["income"] for item in data)
        total_expenses = sum(item["expenses"] for item in data)
        total_transactions = len(all_tx)

        return jsonify(
            {
                "status": "success",
                "data": data,
                "metadata": {
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "total_transactions": total_transactions,
                },
            }
        ), 200

    except Exception as e:
        logger.error(f"Error in cash flow: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/net_assets", methods=["GET"])
def get_net_assets():
    """
    Return trended net asset values over time. Normalizes balances such that
    liabilities reduce net worth (appear negative), and assets increase it.
    """
    today = datetime.utcnow().date()
    months = [today - timedelta(days=30 * i) for i in reversed(range(6))]

    data = []

    for month in months:
        accounts = db.session.query(Account).filter(Account.created_at <= month).all()

        net = sum(
            normalize_account_balance(
                acc.balance if acc.balance is not None else 0, acc.type
            )
            for acc in accounts
        )

        assets = sum(
            acc.balance
            for acc in accounts
            if acc.type.lower() not in ["credit", "loan", "liability"]
            and acc.balance is not None
        )

        liabilities = sum(
            acc.balance
            for acc in accounts
            if acc.type.lower() in ["credit", "credit card", "loan", "liability"]
            and acc.balance is not None
        )

        data.append(
            {
                "date": month.isoformat(),
                "net_assets": net,
                "assets": assets,
                "liabilities": liabilities,
            }
        )

    return jsonify(data)


@charts.route("/daily_net", methods=["GET"])
def get_daily_net():
    try:
        today = datetime.now().date()
        start_date = today - timedelta(days=30)

        transactions = (
            db.session.query(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .filter(Transaction.date >= start_date)
            .all()
        )

        day_map = {}
        for tx in transactions:
            day_str = tx.date.strftime("%Y-%m-%d")
            amt = normalize_account_balance(tx.amount, tx.account.subtype)
            if day_str not in day_map:
                day_map[day_str] = {
                    "net": 0,
                    "income": 0,
                    "expenses": 0,
                    "transaction_count": 0,
                }
            day_map[day_str]["transaction_count"] += 1
            if amt > 0:
                day_map[day_str]["income"] += amt
            else:
                day_map[day_str]["expenses"] += abs(amt)
            day_map[day_str]["net"] += amt

        data = []
        current = start_date
        while current <= today:
            key = current.strftime("%Y-%m-%d")
            entry = day_map.get(
                key, {"net": 0, "income": 0, "expenses": 0, "transaction_count": 0}
            )
            data.append(
                {
                    "date": key,
                    "net": round(entry["net"], 2),
                    "income": round(entry["income"], 2),
                    "expenses": round(entry["expenses"], 2),
                    "transaction_count": entry["transaction_count"],
                }
            )
            current += timedelta(days=1)

        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        logger.error(f"Error in daily net: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/accounts-snapshot", methods=["GET"])
def accounts_snapshot():
    user_id = request.args.get("user_id")
    accounts = (
        db.session.query(Account)
        .filter(Account.user_id == user_id)
        .order_by(Account.balance.desc())
        .all()
    )

    result = [
        {
            "account_id": acc.account_id,
            "name": acc.name,
            "institution_name": acc.institution_name,
            "balance": normalize_account_balance(acc.balance, acc.type),
            "type": acc.type,
            "subtype": acc.subtype,
        }
        for acc in accounts
    ]
    return jsonify(result)
